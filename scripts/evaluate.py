import argparse
import asyncio
import json
import logging
import time
from pathlib import Path

import httpx
from dotenv import find_dotenv, load_dotenv

from src.utils.metrics import (evaluate_explanation_match,
                               generate_confusion_matrix_image)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Evaluation")


async def process_claim(claim_dir: Path, claim_num: int, api_url: str):
    try:
        start_time = time.time()
        
        description_path = claim_dir / "description.txt"
        
        metadata_files = list(claim_dir.glob("*.md"))
        metadata_content = ""
        for md_file in metadata_files:
            if md_file.name != "answer.json":
                with open(md_file, 'r', encoding='utf-8') as f:
                    metadata_content += f"\n\n### {md_file.name}\n\n" + f.read()
        
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp', '*.tiff']
        image_file = None
        for ext in image_extensions:
            images = list(claim_dir.glob(ext))
            if images:
                image_file = images[0]
                break
        
        files = {
            'claim_message': ('description.txt', open(description_path, 'rb'), 'text/plain'),
            'claim_metadata': ('metadata.md', metadata_content.encode('utf-8'), 'text/markdown')
        }
        
        if image_file:
            files['claim_image'] = (image_file.name, open(image_file, 'rb'), 'image/webp')
            logger.info(f"Claim {claim_num}: Submitting with image")
        else:
            logger.info(f"Claim {claim_num}: Submitting without image")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{api_url}/claims", files=files)
            response.raise_for_status()
            api_response = response.json()
        
        execution_time = time.time() - start_time
        
        answer_path = claim_dir / "answer.json"
        with open(answer_path, 'r') as f:
            expected = json.load(f)
        
        predicted_decision = api_response.get('decision')
        predicted_explanation = api_response.get('explanation', '')
        expected_decision = expected['decision']
        expected_explanation = expected.get('explanation', '')
        
        is_correct = predicted_decision == expected_decision
        
        if not is_correct and 'acceptable_decision' in expected:
            is_correct = predicted_decision == expected['acceptable_decision']
        
        explanation_eval = evaluate_explanation_match(predicted_explanation, expected_explanation)
        
        result = {
            "claim_num": claim_num,
            "predicted_decision": predicted_decision,
            "predicted_explanation": predicted_explanation,
            "expected_decision": expected_decision,
            "expected_explanation": expected_explanation,
            "is_correct": is_correct,
            "execution_time_seconds": round(execution_time, 2),
            "explanation_score": explanation_eval.get('score'),
            "explanation_evaluation": explanation_eval.get('reasoning', '')
        }
        
        if 'acceptable_decision' in expected:
            result["expected_acceptable_decision"] = expected['acceptable_decision']
        
        status = "CORRECT" if is_correct else "WRONG"
        exp_score = explanation_eval.get('score')
        exp_info = f", Explanation score: {exp_score}" if exp_score is not None else ""
        logger.info(f"Claim {claim_num}: {status} - Predicted: {predicted_decision}, Expected: {expected_decision}{exp_info}")
        
        for file_tuple in files.values():
            if hasattr(file_tuple[1], 'close'):
                file_tuple[1].close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing claim {claim_num}: {str(e)}")
        return {
            "claim_num": claim_num,
            "error": str(e),
            "is_correct": False
        }


async def evaluate_dataset(dataset_path: str, output_path: str, api_url: str):
    dataset_dir = Path(dataset_path)
    
    if not dataset_dir.exists():
        logger.error(f"Dataset path does not exist: {dataset_path}")
        return
    
    logger.info(f"Starting eval")
    logger.info("="*30)
    
    # Collect all tasks to run concurrently
    tasks = []
    for i in range(1, 26):
        claim_dir = dataset_dir / f"claim {i}"
        if claim_dir.exists():
            tasks.append(process_claim(claim_dir, i, api_url))
        else:
            logger.warning(f"Claim directory not found: {claim_dir}")
    
    # Run all claims concurrently
    results = await asyncio.gather(*tasks)
    
    total_claims = len(results)
    correct_predictions = sum(1 for r in results if r.get('is_correct', False))
    accuracy = (correct_predictions / total_claims * 100) if total_claims > 0 else 0
    
    # Calculate average execution time
    execution_times = [r.get('execution_time_seconds', 0) for r in results if 'execution_time_seconds' in r]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    
    # Calculate average explanation score (excluding None values)
    explanation_scores = [r.get('explanation_score') for r in results if r.get('explanation_score') is not None]
    avg_explanation_score = sum(explanation_scores) / len(explanation_scores) if explanation_scores else None
    
    # Create summary statistics
    summary = {
        "summary": {
            "accuracy": round(accuracy, 2),
            "correct_predictions": correct_predictions,
            "total_claims": total_claims,
            "average_execution_time_seconds": round(avg_execution_time, 2),
            "average_explanation_score": round(avg_explanation_score, 2) if avg_explanation_score is not None else None,
            "explanation_scores_evaluated": len(explanation_scores)
        }
    }
    
    logger.info("")
    logger.info(f"Accuracy: {correct_predictions}/{total_claims} ({accuracy:.2f}%)")
    logger.info(f"Average execution time: {avg_execution_time:.2f}s")
    if avg_explanation_score is not None:
        logger.info(f"Average explanation score: {avg_explanation_score:.2f} ({len(explanation_scores)} evaluated)")
    
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    confusion_matrix_path = output_dir / "confusion_matrix.png"
    generate_confusion_matrix_image(results, str(confusion_matrix_path))
    
    # Save results JSON with summary as first element
    results_file = output_dir / "eval_results.json"
    final_output = [summary] + results
    with open(results_file, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"Results: {results_file}")
    logger.info(f"Confusion matrix: {confusion_matrix_path}")


def get_arguments():
    parser = argparse.ArgumentParser(description="Evals claims processing agent")
    parser.add_argument(
        "-d", "--dataset",
        type=str,
        default="takehome-test-data",
        help="Path to test dataset"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="results",
        help="Output directory for results"
    )
    parser.add_argument(
        "-u", "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL"
    )
    return parser.parse_args()


def main():
    args = get_arguments()
    asyncio.run(evaluate_dataset(args.dataset, args.output_dir, args.api_url))


if __name__ == "__main__":
    main()

import argparse
import asyncio
import json
import logging
from pathlib import Path

import httpx

from src.utils.metrics import generate_confusion_matrix_image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Evaluation")


async def process_claim(claim_dir: Path, claim_num: int, api_url: str):
    try:
        # Read claim description
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
        
        answer_path = claim_dir / "answer.json"
        with open(answer_path, 'r') as f:
            expected = json.load(f)
        
        predicted_decision = api_response.get('decision')
        predicted_explanation = api_response.get('explanation', '')
        expected_decision = expected['decision']
        
        is_correct = predicted_decision == expected_decision
        
        if not is_correct and 'acceptable_decision' in expected:
            is_correct = predicted_decision == expected['acceptable_decision']
        
        result = {
            "claim_num": claim_num,
            "predicted_decision": predicted_decision,
            "predicted_explanation": predicted_explanation,
            "expected_decision": expected_decision,
            "expected_explanation": expected.get('explanation', ''),
            "is_correct": is_correct
        }
        
        status = "CORRECT" if is_correct else "WRONG"
        logger.info(f"Claim {claim_num}: {status} - Predicted: {predicted_decision}, Expected: {expected_decision}")
        
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
    
    results = []
    
    for i in range(1, 26):
        claim_dir = dataset_dir / f"claim {i}"
        if claim_dir.exists():
            result = await process_claim(claim_dir, i, api_url)
            results.append(result)
        else:
            logger.warning(f"Claim directory not found: {claim_dir}")
    
    total_claims = len(results)
    correct_predictions = sum(1 for r in results if r.get('is_correct', False))
    accuracy = (correct_predictions / total_claims * 100) if total_claims > 0 else 0
    print(f"\nAccuracy: {correct_predictions}/{total_claims} ({accuracy:.2f}%)")
    
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    confusion_matrix_path = output_dir / "confusion_matrix.png"
    generate_confusion_matrix_image(results, str(confusion_matrix_path))
    
    # Save simplified results JSON
    results_file = output_dir / "eval_results.json"
    simplified_results = []
    for r in results:
        result_entry = {
            "claim": f"claim {r['claim_num']}",
            "decision": r.get('predicted_decision', 'ERROR'),
            "reason": r.get('predicted_explanation', r.get('error', 'Unknown error')),
            "gt_decision": r.get('expected_decision', ''),
        }
        
        # Add gt_reason only if present
        gt_explanation = r.get('expected_explanation', '')
        if gt_explanation:
            result_entry["gt_reason"] = gt_explanation
        
        simplified_results.append(result_entry)
    
    with open(results_file, 'w') as f:
        json.dump(simplified_results, f, indent=2)
    
    print(f"Results: {results_file}")
    print(f"Confusion matrix: {confusion_matrix_path}")


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

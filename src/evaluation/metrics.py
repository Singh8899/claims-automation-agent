from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def calculate_confusion_matrix(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    decisions = ["APPROVE", "DENY", "UNCERTAIN"]
    matrix = {d: {d2: 0 for d2 in decisions} for d in decisions}
    
    for result in results:
        if 'error' in result:
            continue
        predicted = result.get('predicted_decision')
        expected = result.get('expected_decision')
        if predicted and expected and predicted in decisions and expected in decisions:
            matrix[expected][predicted] += 1
    
    return matrix


def generate_confusion_matrix_image(results: List[Dict[str, Any]], output_path: str = "confusion_matrix.png"):
    matrix_dict = calculate_confusion_matrix(results)
    decisions = ["APPROVE", "DENY", "UNCERTAIN"]
    
    # Convert to numpy array
    matrix = np.array([[matrix_dict[exp][pred] for pred in decisions] for exp in decisions])
    
    # Create figure
    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues', 
                xticklabels=decisions, yticklabels=decisions,
                cbar_kws={'label': 'Count'}, linewidths=1, linecolor='gray')
    
    plt.xlabel('Predicted Decision', fontsize=12, fontweight='bold')
    plt.ylabel('Expected Decision', fontsize=12, fontweight='bold')
    plt.title('Confusion Matrix - Claims Processing Evaluation', fontsize=14, fontweight='bold', pad=20)
    
    # Add accuracy text
    total = matrix.sum()
    correct = np.trace(matrix)
    accuracy = (correct / total * 100) if total > 0 else 0
    plt.text(0.5, -0.15, f'Overall Accuracy: {accuracy:.2f}% ({correct}/{total})', 
             transform=plt.gca().transAxes, ha='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

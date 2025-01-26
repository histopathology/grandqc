import os
import numpy as np
from PIL import Image
import pandas as pd
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

class GrandQCAnalyzer:
    """
    A class to analyze GrandQC mask outputs and calculate artifact percentages.
    """
    def __init__(self):
        # Define the class mapping based on GrandQC documentation
        self.artifact_classes = {
            1: "Normal Tissue",
            2: "Tissue Fold",
            3: "Dark Spot/Foreign",
            4: "Pen Marking",
            5: "Air Bubble/Edge",
            6: "Out of Focus",
            7: "Background"
        }
        
    def analyze_mask(self, mask_path: str) -> Dict[str, float]:
        """
        Analyze a single mask file and return percentage of each artifact type.
        
        Args:
            mask_path: Path to the mask PNG file
            
        Returns:
            Dictionary with artifact types and their percentages
        """
        # Read the mask
        mask = np.array(Image.open(mask_path))
        
        # Get total non-background pixels (class 7 is background)
        total_tissue_pixels = np.sum(mask != 7)
        
        if total_tissue_pixels == 0:
            return {self.artifact_classes[i]: 0.0 for i in range(1, 7)}
            
        # Calculate percentages for each class
        percentages = {}
        for class_idx, class_name in self.artifact_classes.items():
            if class_idx != 7:  # Skip background
                pixels = np.sum(mask == class_idx)
                percentage = (pixels / total_tissue_pixels) * 100
                percentages[class_name] = round(percentage, 2)
                
        return percentages
    
    def analyze_directory(self, mask_dir: str) -> pd.DataFrame:
        """
        Analyze all mask files in a directory.
        
        Args:
            mask_dir: Directory containing mask PNG files
            
        Returns:
            DataFrame with analysis results for all slides
        """
        results = []
        
        # Process each mask file
        for filename in os.listdir(mask_dir):
            if filename.endswith("_mask.png"):
                mask_path = os.path.join(mask_dir, filename)
                percentages = self.analyze_mask(mask_path)
                
                # Add filename to results
                result_row = {"Slide": filename.replace("_mask.png", "")}
                result_row.update(percentages)
                results.append(result_row)
                
        # Convert to DataFrame
        return pd.DataFrame(results)
    
    def generate_report(self, df: pd.DataFrame, output_dir: str):
        """
        Generate analysis report with visualizations.
        
        Args:
            df: DataFrame with analysis results
            output_dir: Directory to save report files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save detailed CSV report
        df.to_csv(os.path.join(output_dir, "artifact_analysis.csv"), index=False)
        
        # Calculate summary statistics
        summary = df.drop("Slide", axis=1).agg(['mean', 'std', 'min', 'max'])
        summary.to_csv(os.path.join(output_dir, "summary_statistics.csv"))
        
        # Generate visualization
        plt.figure(figsize=(12, 6))
        box_data = [df[col] for col in df.columns if col != "Slide"]
        plt.boxplot(box_data, labels=[col for col in df.columns if col != "Slide"])
        plt.xticks(rotation=45)
        plt.title("Distribution of Artifact Percentages Across Slides")
        plt.ylabel("Percentage")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "artifact_distribution.png"))
        plt.close()

def main():
    # Example usage
    analyzer = GrandQCAnalyzer()
    
    # Replace with your mask directory path
    mask_dir = "/path/to/mask_qc"
    output_dir = "/path/to/analysis_output"
    
    # Run analysis
    results_df = analyzer.analyze_directory(mask_dir)
    analyzer.generate_report(results_df, output_dir)
    
    # Print summary to console
    print("\nAnalysis Summary:")
    print("-" * 50)
    print(f"Total slides analyzed: {len(results_df)}")
    print("\nMean artifact percentages:")
    for col in results_df.columns:
        if col != "Slide":
            mean_val = results_df[col].mean()
            print(f"{col}: {mean_val:.2f}%")

if __name__ == "__main__":
    main()
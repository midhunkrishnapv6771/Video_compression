"""
apti_compress.metrics
======================
SSIM / PSNR visual quality evaluation.
"""

def compute_ssim_psnr(original_path: str, compressed_path: str) -> dict:
    """Compute SSIM and PSNR metrics between original and compressed video."""
    # Placeholder implementation
    return {"ssim": 0.95, "psnr": 35.0}

def evaluate_quality_gate(metrics: dict, threshold: float = 0.9) -> bool:
    """Evaluate if quality metrics meet the threshold."""
    return metrics.get("ssim", 0) >= threshold

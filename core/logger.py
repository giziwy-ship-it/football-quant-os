#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Naga Quant - Unified Logging System
Replaces 4393 print() statements with structured logging
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

# Default log directory (relative to workspace)
DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
DEFAULT_LOG_DIR.mkdir(exist_ok=True)


def setup_logging(
    name: str = "naga_quant",
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup structured logging with rotation.
    
    Args:
        name: logger name (usually __name__)
        level: logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_dir: directory for log files (default: workspace/logs/)
        console: output to stdout
        file: output to rotating file
        max_bytes: max log file size before rotation
        backup_count: number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if file:
        log_dir = log_dir or DEFAULT_LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Convenience function for quick setup
def get_logger(name: str = "naga_quant") -> logging.Logger:
    """Get or create logger. If not configured, sets up with defaults."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logging(name)
    return logger


# Module-level logger for core module
logger = get_logger("naga_quant.core")

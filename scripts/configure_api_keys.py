#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - API Key Configuration Helper

Helps user configure API keys for:
- API-Football (100 calls/day free)
- Football-Data.org (free with registration)

Usage:
    python configure_api_keys.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.api_config import configure_api_key, check_api_status, create_config_template


def show_menu():
    """Display configuration menu"""
    print("=" * 60)
    print("Football Quant OS - API Key Configuration")
    print("=" * 60)
    
    status = check_api_status()
    
    print("\nCurrent Status:")
    for service, configured in status.items():
        icon = "ON" if configured else "OFF"
        print(f"  [{icon}] {service}")
    
    print("\nOptions:")
    print("  1. Configure API-Football Key")
    print("  2. Configure Football-Data.org Key")
    print("  3. Check configuration status")
    print("  4. Create config template")
    print("  5. Exit")
    
    return input("\nSelect option (1-5): ").strip()


def configure_api_football():
    """Configure API-Football key"""
    print("\n" + "-" * 40)
    print("API-Football Configuration")
    print("-" * 40)
    print("Get free key at: https://www.api-football.com/")
    print("Free tier: 100 calls/day")
    print("Supports: Real-time matches, xG, possession, odds")
    
    key = input("\nEnter your API-Football key: ").strip()
    
    if key:
        configure_api_key('api_football', key)
        print("\nAPI-Football key configured successfully!")
    else:
        print("\nNo key entered. Skipping.")


def configure_football_data_org():
    """Configure Football-Data.org key"""
    print("\n" + "-" * 40)
    print("Football-Data.org Configuration")
    print("-" * 40)
    print("Get free key at: https://www.football-data.org/")
    print("Free tier: Unlimited (with registration)")
    print("Supports: Historical odds, fixtures, team info")
    
    key = input("\nEnter your Football-Data.org key: ").strip()
    
    if key:
        configure_api_key('football_data_org', key)
        print("\nFootball-Data.org key configured successfully!")
    else:
        print("\nNo key entered. Skipping.")


def check_status():
    """Check and display configuration status"""
    print("\n" + "-" * 40)
    print("Configuration Status")
    print("-" * 40)
    
    status = check_api_status()
    
    for service, configured in status.items():
        if configured:
            print(f"  [OK] {service}: Configured")
        else:
            print(f"  [MISSING] {service}: Not configured")
    
    all_configured = all(status.values())
    
    if all_configured:
        print("\nAll APIs configured! Ready to use.")
    else:
        print("\nSome APIs missing. Configure them for full functionality.")
        print("You can still use local data (Kaggle) without API keys.")


def create_template():
    """Create configuration template"""
    template_path = create_config_template()
    print(f"\nConfig template created at: {template_path}")
    print("Edit this file to add your API keys.")


def main():
    """Main configuration helper"""
    while True:
        choice = show_menu()
        
        if choice == '1':
            configure_api_football()
        elif choice == '2':
            configure_football_data_org()
        elif choice == '3':
            check_status()
        elif choice == '4':
            create_template()
        elif choice == '5':
            print("\nExiting configuration helper.")
            print("Run this script again anytime to update keys.")
            break
        else:
            print("\nInvalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == '__main__':
    main()

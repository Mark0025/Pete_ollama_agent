#!/usr/bin/env python3
"""
DateTime Utilities using Pendulum
================================

Provides robust datetime handling with timezone support, formatting,
and conversion utilities for the PeteOllama application.
"""

import pendulum
from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta

# Default timezone for the application (Central Standard Time)
DEFAULT_TIMEZONE = "America/Chicago"

class DateTimeUtils:
    """Utility class for datetime operations using Pendulum"""
    
    @staticmethod
    def now(tz: str = DEFAULT_TIMEZONE) -> pendulum.DateTime:
        """Get current time in specified timezone"""
        return pendulum.now(tz)
    
    @staticmethod
    def now_cst() -> pendulum.DateTime:
        """Get current time in Central Standard Time"""
        return pendulum.now(DEFAULT_TIMEZONE)
    
    @staticmethod
    def format_datetime(dt: Union[datetime, pendulum.DateTime, str], 
                       format_str: str = "YYYY-MM-DD HH:mm:ss",
                       tz: str = DEFAULT_TIMEZONE) -> str:
        """
        Format datetime to string with specified format
        
        Args:
            dt: Datetime object, string, or pendulum DateTime
            format_str: Pendulum format string
            tz: Target timezone
            
        Returns:
            Formatted datetime string
        """
        if isinstance(dt, str):
            # Parse string to pendulum DateTime
            dt = pendulum.parse(dt)
        elif isinstance(dt, datetime):
            # Convert Python datetime to pendulum
            dt = pendulum.instance(dt)
        
        # Convert to target timezone and format
        return dt.in_tz(tz).format(format_str)
    
    @staticmethod
    def format_for_display(dt: Union[datetime, pendulum.DateTime, str], 
                          tz: str = DEFAULT_TIMEZONE) -> str:
        """
        Format datetime for user-friendly display
        
        Args:
            dt: Datetime object, string, or pendulum DateTime
            tz: Target timezone
            
        Returns:
            User-friendly formatted string
        """
        if isinstance(dt, str):
            dt = pendulum.parse(dt)
        elif isinstance(dt, datetime):
            dt = pendulum.instance(dt)
        
        dt_cst = dt.in_tz(tz)
        now = pendulum.now(tz)
        
        # If it's today, show time
        if dt_cst.date() == now.date():
            return f"Today at {dt_cst.format('h:mm A')}"
        
        # If it's yesterday
        if dt_cst.date() == now.date() - timedelta(days=1):
            return f"Yesterday at {dt_cst.format('h:mm A')}"
        
        # If it's this week
        if dt_cst.date() >= now.date() - timedelta(days=7):
            return dt_cst.format("dddd at h:mm A")
        
        # If it's this year
        if dt_cst.year == now.year:
            return dt_cst.format("MMM D at h:mm A")
        
        # Otherwise show full date
        return dt_cst.format("MMM D, YYYY at h:mm A")
    
    @staticmethod
    def format_for_api(dt: Union[datetime, pendulum.DateTime, str], 
                      tz: str = DEFAULT_TIMEZONE) -> str:
        """
        Format datetime for API responses (ISO format)
        
        Args:
            dt: Datetime object, string, or pendulum DateTime
            tz: Target timezone
            
        Returns:
            ISO formatted datetime string
        """
        if isinstance(dt, str):
            dt = pendulum.parse(dt)
        elif isinstance(dt, datetime):
            dt = pendulum.instance(dt)
        
        return dt.in_tz(tz).isoformat()
    
    @staticmethod
    def format_for_filename(dt: Union[datetime, pendulum.DateTime, str], 
                           tz: str = DEFAULT_TIMEZONE) -> str:
        """
        Format datetime for safe filename usage
        
        Args:
            dt: Datetime object, string, or pendulum DateTime
            tz: Target timezone
            
        Returns:
            Safe filename datetime string
        """
        if isinstance(dt, str):
            dt = pendulum.parse(dt)
        elif isinstance(dt, datetime):
            dt = pendulum.instance(dt)
        
        return dt.in_tz(tz).format("YYYYMMDD_HHmmss")
    
    @staticmethod
    def parse_datetime(dt_str: str, tz: str = DEFAULT_TIMEZONE) -> pendulum.DateTime:
        """
        Parse datetime string to pendulum DateTime
        
        Args:
            dt_str: Datetime string to parse
            tz: Target timezone
            
        Returns:
            Parsed pendulum DateTime object
        """
        return pendulum.parse(dt_str).in_tz(tz)
    
    @staticmethod
    def get_time_ago(dt: Union[datetime, pendulum.DateTime, str], 
                     tz: str = DEFAULT_TIMEZONE) -> str:
        """
        Get human-readable time ago string
        
        Args:
            dt: Datetime object, string, or pendulum DateTime
            tz: Target timezone
            
        Returns:
            Human-readable time ago string
        """
        if isinstance(dt, str):
            dt = pendulum.parse(dt)
        elif isinstance(dt, datetime):
            dt = pendulum.instance(dt)
        
        dt_cst = dt.in_tz(tz)
        now = pendulum.now(tz)
        
        diff = now - dt_cst
        
        if diff.in_seconds() < 60:
            return "just now"
        elif diff.in_minutes() < 60:
            minutes = int(diff.in_minutes())
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.in_hours() < 24:
            hours = int(diff.in_hours())
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.in_days() < 7:
            days = int(diff.in_days())
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif diff.in_weeks() < 4:
            weeks = int(diff.in_weeks())
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = int(diff.in_months())
            return f"{months} month{'s' if months != 1 else ''} ago"
    
    @staticmethod
    def get_cst_timezone_info() -> Dict[str, Any]:
        """
        Get current CST timezone information
        
        Returns:
            Dictionary with timezone info
        """
        now = pendulum.now(DEFAULT_TIMEZONE)
        
        return {
            "timezone": DEFAULT_TIMEZONE,
            "current_time": now.format("YYYY-MM-DD HH:mm:ss"),
            "current_time_display": now.format("h:mm A"),
            "current_date": now.format("dddd, MMMM D, YYYY"),
            "is_dst": now.is_dst(),
            "offset": now.offset_hours,
            "abbreviation": "CST" if not now.is_dst() else "CDT"
        }
    
    @staticmethod
    def convert_timezone(dt: Union[datetime, pendulum.DateTime, str], 
                        from_tz: str, to_tz: str) -> pendulum.DateTime:
        """
        Convert datetime between timezones
        
        Args:
            dt: Datetime object, string, or pendulum DateTime
            from_tz: Source timezone
            to_tz: Target timezone
            
        Returns:
            Converted pendulum DateTime object
        """
        if isinstance(dt, str):
            dt = pendulum.parse(dt)
        elif isinstance(dt, datetime):
            dt = pendulum.instance(dt)
        
        return dt.in_tz(from_tz).in_tz(to_tz)

# Convenience functions for common operations
def now_cst() -> pendulum.DateTime:
    """Get current time in CST"""
    return DateTimeUtils.now_cst()

def format_datetime_display(dt: Union[datetime, pendulum.DateTime, str]) -> str:
    """Format datetime for user-friendly display in CST"""
    return DateTimeUtils.format_for_display(dt)

def format_datetime_api(dt: Union[datetime, pendulum.DateTime, str]) -> str:
    """Format datetime for API responses in CST"""
    return DateTimeUtils.format_for_api(dt)

def format_datetime_filename(dt: Union[datetime, pendulum.DateTime, str]) -> str:
    """Format datetime for safe filename usage in CST"""
    return DateTimeUtils.format_for_filename(dt)

def get_time_ago_cst(dt: Union[datetime, pendulum.DateTime, str]) -> str:
    """Get human-readable time ago string in CST"""
    return DateTimeUtils.get_time_ago(dt)

def get_cst_info() -> Dict[str, Any]:
    """Get current CST timezone information"""
    return DateTimeUtils.get_cst_timezone_info()

# Example usage and testing
if __name__ == "__main__":
    print("🕐 DateTime Utilities Test")
    print("=" * 40)
    
    # Test current time
    now = now_cst()
    print(f"Current CST time: {now.format('YYYY-MM-DD HH:mm:ss')}")
    
    # Test formatting
    test_time = "2025-08-19T15:30:00Z"
    print(f"Test time: {test_time}")
    print(f"Display format: {format_datetime_display(test_time)}")
    print(f"API format: {format_datetime_api(test_time)}")
    print(f"Filename format: {format_datetime_filename(test_time)}")
    print(f"Time ago: {get_time_ago_cst(test_time)}")
    
    # Test timezone info
    tz_info = get_cst_info()
    print(f"\nTimezone info: {tz_info}")

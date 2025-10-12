#!/usr/bin/env python3
"""
Test script for TTS text cleaning functionality
"""

import sys
import os
import re

# Add the current directory to the path so we can import from app.py
sys.path.append(os.path.dirname(__file__))

def clean_text_for_tts(text: str) -> str:
    """
    Clean text for TTS by removing markdown formatting and special characters
    that cause pronunciation issues.
    """
    if not text:
        return text
    
    # Remove markdown formatting
    # Remove bold formatting (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove italic formatting (*text* or _text_)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove code formatting (`text`)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove strikethrough formatting (~~text~~)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Remove headers (# ## ###)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove links but keep the text ([text](url) -> text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove blockquotes (> text)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules (--- or ***)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Remove list markers (- * + 1. 2. etc.)
    text = re.sub(r'^[\s]*[-*+]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single
    text = re.sub(r'[ \t]+', ' ', text)    # Multiple spaces to single
    text = re.sub(r'\n ', '\n', text)      # Remove leading spaces after newlines
    
    # Remove any remaining special characters that might cause issues
    # Keep common punctuation but remove problematic ones
    text = re.sub(r'[^\w\s.,!?;:\-"\']', '', text)
    
    # Clean up multiple spaces again after character removal
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Clean up the final result
    text = text.strip()
    
    return text

def test_text_cleaning():
    """Test the text cleaning function with various markdown and special characters"""
    
    test_cases = [
        {
            "input": "Yes, I am **connected to Spotify** right now, connected as **ben.petlach**!",
            "expected": "Yes, I am connected to Spotify right now, connected as ben.petlach!",
            "description": "Bold markdown formatting"
        },
        {
            "input": "Here's a *italic* text and some `code` formatting.",
            "expected": "Here's a italic text and some code formatting.",
            "description": "Italic and code formatting"
        },
            {
            "input": "## This is a header\n\n- List item 1\n- List item 2\n\nRegular text.",
            "expected": "This is a header\nList item 1\nList item 2\nRegular text.",
            "description": "Headers and list formatting"
        },
        {
            "input": "Check out [this link](https://example.com) for more info.",
            "expected": "Check out this link for more info.",
            "description": "Link formatting"
        },
        {
            "input": "> This is a blockquote\n\nNormal text after.",
            "expected": "This is a blockquote\nNormal text after.",
            "description": "Blockquote formatting"
        },
        {
            "input": "Text with @#$%^&*() special characters!",
            "expected": "Text with special characters!",
            "description": "Special characters removal"
        },
        {
            "input": "Multiple    spaces   and\n\n\nnewlines.",
            "expected": "Multiple spaces and\nnewlines.",
            "description": "Multiple spaces and newlines cleanup"
        },
        {
            "input": "Mixed **bold** and *italic* with `code` and [links](url).",
            "expected": "Mixed bold and italic with code and links.",
            "description": "Mixed markdown formatting"
        },
        {
            "input": "1. First item\n2. Second item\n3. Third item",
            "expected": "First item\nSecond item\nThird item",
            "description": "Numbered list formatting"
        },
        {
            "input": "Text with ~~strikethrough~~ and normal text.",
            "expected": "Text with strikethrough and normal text.",
            "description": "Strikethrough formatting"
        }
    ]
    
    print("🧪 Testing TTS Text Cleaning Function")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Input:    '{test_case['input']}'")
        
        result = clean_text_for_tts(test_case['input'])
        print(f"   Output:   '{result}'")
        print(f"   Expected: '{test_case['expected']}'")
        
        if result == test_case['expected']:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Text cleaning function is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

def test_real_world_example():
    """Test with the real-world example from the user's issue"""
    print("\n🌍 Testing Real-World Example")
    print("-" * 40)
    
    real_text = "Gemini direct response: Yes, I am **connected to Spotify** right now, connected as **ben.petlach**!"
    cleaned = clean_text_for_tts(real_text)
    
    print(f"Original:  '{real_text}'")
    print(f"Cleaned:   '{cleaned}'")
    
    # Check if asterisks are removed
    if "**" not in cleaned and "*" not in cleaned:
        print("✅ Asterisks successfully removed!")
        return True
    else:
        print("❌ Asterisks still present in cleaned text!")
        return False

if __name__ == "__main__":
    # Run the main test suite
    test_result = test_text_cleaning()
    
    # Run the real-world example test
    real_world_result = test_real_world_example()
    
    # Overall result
    if test_result == 0 and real_world_result:
        print("\n🎉 All tests passed! The TTS text cleaning is ready for production.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please fix the implementation.")
        sys.exit(1)

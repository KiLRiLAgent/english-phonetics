#!/usr/bin/env python3
"""Analyze lecture video."""

import sys
from analyzer_simple import SimpleAnalyzer

if __name__ == "__main__":
    video_file = "Lecture_01_Igor Lyubimov_21.01.mp4"
    
    print(f"🎬 Analyzing lecture: {video_file}")
    print("⏳ This will take 10-15 minutes for a 1.7GB video...")
    
    # Initialize analyzer
    analyzer = SimpleAnalyzer()
    
    # Analyze
    result = analyzer.analyze(video_file)
    
    # Save result
    output_file = "lecture_result.json"
    analyzer.save_result(result, output_file)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 ANALYSIS COMPLETE")
    print("="*80)
    print(f"Score: {result['score']}/100")
    print(f"Errors found: {len(result['errors'])}")
    print(f"Transcript length: {len(result['transcript'])} chars")
    print(f"\nFirst 500 chars:")
    print(result['transcript'][:500])
    
    if result['errors']:
        print(f"\n❌ Top 10 errors:")
        for i, err in enumerate(result['errors'][:10], 1):
            mins = int(err['timestamp'] // 60)
            secs = int(err['timestamp'] % 60)
            print(f"\n{i}. [{mins}:{secs:02d}] \"{err['text']}\"")
            print(f"   → {err['message']}")
    
    print(f"\n💾 Full results saved to: {output_file}")
    print(f"🌐 Open web UI: http://localhost:8780/history.html")

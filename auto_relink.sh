#!/bin/bash
# Auto-relink errors when word-level transcript is ready

cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer

echo "Waiting for word-level transcript to complete..."

# Wait for transcript to be created
while [ ! -f "transcriptions/Lecture_01_Igor Lyubimov_21.01_words.json" ]; do
    sleep 10
done

echo "✅ Word-level transcript found!"
sleep 2

# Relink errors
echo "Relinking grammar errors to word timestamps..."
python3 link_to_words.py \
    "transcriptions/Lecture_01_Igor Lyubimov_21.01_20260221_164529.grammar.full.json" \
    "transcriptions/Lecture_01_Igor Lyubimov_21.01_words.json"

echo ""
echo "✅ Done! Restarting server..."
pkill -f lecture_server.py
sleep 1
python3 lecture_server.py > /tmp/lecture_server.log 2>&1 &

echo "✅ Server restarted with word-level timestamps"
echo "   Refresh http://localhost:8899/grammar to see accurate timings"

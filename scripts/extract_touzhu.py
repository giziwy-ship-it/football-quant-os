#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

with open("500_1359189_full_20260613_072809.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract and save touzhu text
with open("touzhu_text.txt", "w", encoding="utf-8") as f:
    f.write(data["pages"]["touzhu"]["text_preview"])

print("touzhu text saved")

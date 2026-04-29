import textwrap
import csv
import re
from typing import List, Dict, Any

class HealthcareChatbot:
    def __init__(self, dataset_path: str = "symptoms_dataset.csv", verbose: bool = True):
        self.name = "Healthcare Chatbot with Symptom Checker"
        self.wrap_width = 80
        self.verbose = verbose
        self.symptom_data = self.load_dataset(dataset_path)
        if self.verbose:
            print(f"[HealthcareChatbot] Loaded {len(self.symptom_data)} symptom entries.")
            for i, it in enumerate(self.symptom_data[:20], start=1):
                print(f"  {i}. keywords={it.get('keywords')} emergency={it.get('emergency')}")

    def load_dataset(self, path: str) -> List[Dict[str, Any]]:
        """
        Load dataset robustly:
        - Accepts CSV with headers (symptom_keywords,explanation,tips,emergency_flag)
        - Or accepts header-less rows with columns: keywords, explanation, tips, [emergency_flag]
        - Skips comment lines starting with '#'
        - Uses utf-8-sig to handle BOM
        """
        data: List[Dict[str, Any]] = []
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                lines = [ln for ln in f.readlines()]

            non_comment_lines = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]

            if not non_comment_lines:
                if self.verbose:
                    print(f"[HealthcareChatbot] No data rows found in {path}.")
                return []

            first = non_comment_lines[0]
            header_like = False
            lower_first = first.lower()
            if ("symptom" in lower_first or "keyword" in lower_first or "explanation" in lower_first) and "," in first:
                header_like = True

            if header_like:
                reader = csv.DictReader(non_comment_lines)
                fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
                for row in reader:
                    if not row:
                        continue
                    raw_keywords = (row.get("symptom_keywords") or row.get("keywords") or row.get("symptoms") or "").strip()
                    raw_explanation = (row.get("explanation") or row.get("explain") or row.get("description") or "").strip()
                    raw_tips = (row.get("tips") or row.get("advice") or "").strip()
                    raw_em_flag = (row.get("emergency_flag") or row.get("em_flag") or "0").strip() or "0"

                    if not raw_keywords or not raw_explanation:
                        continue

                    keywords = [kw.strip().lower() for kw in re.split(r"[|,;]", raw_keywords) if kw and kw.strip()]
                    if not keywords:
                        continue

                    escaped = [re.escape(k) for k in keywords if k]
                    pattern = None
                    if escaped:
                        pat_text = r"\b(?:" + "|".join(escaped) + r")\b"
                        try:
                            pattern = re.compile(pat_text, flags=re.IGNORECASE)
                        except re.error:
                            pattern = re.compile("|".join(escaped), flags=re.IGNORECASE)

                    data.append({
                        "keywords": keywords,
                        "pattern": pattern,
                        "explanation": raw_explanation,
                        "tips": raw_tips,
                        "emergency": str(raw_em_flag).strip() == "1",
                    })
            else:
                reader = csv.reader(non_comment_lines)
                for row in reader:
                    if not row:
                        continue

                    cols = [c.strip() for c in row]
                    if len(cols) < 2:
                        joined = cols[0] if cols else ""
                        split_alt = [c.strip() for c in re.split(r"\s*,\s*|\s*\|\s*|\s*;\s*", joined) if c.strip()]
                        if len(split_alt) >= 2:
                            cols = split_alt
                        else:
                            continue

                    raw_keywords = cols[0]
                    raw_explanation = cols[1] if len(cols) >= 2 else ""
                    raw_tips = cols[2] if len(cols) >= 3 else ""
                    raw_em_flag = cols[3] if len(cols) >= 4 else "0"

                    if not raw_keywords or not raw_explanation:
                        continue

                    keywords = [kw.strip().lower() for kw in re.split(r"[|,;]", raw_keywords) if kw and kw.strip()]
                    if not keywords:
                        continue

                    escaped = [re.escape(k) for k in keywords if k]
                    pattern = None
                    if escaped:
                        pat_text = r"\b(?:" + "|".join(escaped) + r")\b"
                        try:
                            pattern = re.compile(pat_text, flags=re.IGNORECASE)
                        except re.error:
                            pattern = re.compile("|".join(escaped), flags=re.IGNORECASE)

                    data.append({
                        "keywords": keywords,
                        "pattern": pattern,
                        "explanation": raw_explanation,
                        "tips": raw_tips,
                        "emergency": str(raw_em_flag).strip() == "1",
                    })

        except FileNotFoundError:
            if self.verbose:
                print(f"[HealthcareChatbot] WARNING: Dataset file '{path}' not found.")
            data = [
                {
                    "keywords": ["fever", "temperature"],
                    "pattern": re.compile(r"\b(?:fever|temperature)\b", flags=re.IGNORECASE),
                    "explanation": "Fever may indicate infection.",
                    "tips": "Rest and drink fluids.",
                    "emergency": False,
                }
            ]
        except Exception as e:
            print(f"[HealthcareChatbot] ERROR reading dataset: {e}")

        return data

    def analyze_symptoms(self, text: str) -> str:
        msg = (text or "").strip()
        if not msg:
            return "Please describe your symptoms."

        lower_msg = msg.lower()
        responses = []

        emergency_msg = self.check_emergency(lower_msg)
        if emergency_msg:
            responses.append(emergency_msg)

        matched_any = False

        for item in self.symptom_data:
            pat = item.get("pattern")
            if pat and pat.search(lower_msg):
                matched_any = True
                responses.append(item.get("explanation", ""))
                tips = item.get("tips", "")
                if tips:
                    responses.append(tips)
                if item.get("emergency") and not emergency_msg:
                    responses.append("⚠️ This symptom may be serious. Please consider consulting a healthcare professional.")

        if not matched_any:
            for item in self.symptom_data:
                for kw in item.get("keywords", []):
                    if kw and kw in lower_msg:
                        matched_any = True
                        responses.append(item.get("explanation", ""))
                        tips = item.get("tips", "")
                        if tips:
                            responses.append(tips)
                        if item.get("emergency") and not emergency_msg:
                            responses.append("⚠️ This symptom may be serious. Please consider consulting a healthcare professional.")
                        break
                if matched_any:
                    break

        if not matched_any:
            responses.append("I couldn't identify symptoms clearly from your message.")
            responses.append("Try describing: your main symptom, your age, and how long you've had it.")

        responses.append("❗ This is general info only. Always consult a qualified medical professional.")
        return "\n\n".join([r for r in responses if r])

    def check_emergency(self, text: str):
        txt = (text or "").lower()
        emergency_keywords = [
            "severe chest pain", "chest pain",
            "difficulty breathing", "shortness of breath",
            "can't breathe", "cannot breathe",
            "unconscious", "fainted",
            "confusion", "heavy bleeding",
            "vomiting blood", "blood in vomit",
            "black stool", "bloody stool", "very high fever"
        ]
        for kw in emergency_keywords:
            try:
                if re.search(r"\b" + re.escape(kw) + r"\b", txt):
                    return (
                        "⚠️ Possible emergency detected.\n"
                        "Please seek immediate medical help or call emergency services.\n"
                        "Do NOT rely on this chatbot for emergency care."
                    )
            except re.error:
                if kw in txt:
                    return (
                        "⚠️ Possible emergency detected.\n"
                        "Please seek immediate medical help or call emergency services.\n"
                        "Do NOT rely on this chatbot for emergency care."
                    )
        return None

    def debug_match(self, text: str):
        lower_msg = (text or "").lower()
        results = {"text": text, "regex_matches": [], "substring_matches": []}
        for item in self.symptom_data:
            pat = item.get("pattern")
            if pat and pat.search(lower_msg):
                results["regex_matches"].append({
                    "keywords": item.get("keywords"),
                    "explanation": item.get("explanation"),
                    "tips": item.get("tips"),
                    "emergency": item.get("emergency"),
                })
        if not results["regex_matches"]:
            for item in self.symptom_data:
                for kw in item.get("keywords", []):
                    if kw and kw in lower_msg:
                        results["substring_matches"].append({
                            "keyword": kw,
                            "keywords": item.get("keywords"),
                            "explanation": item.get("explanation"),
                            "tips": item.get("tips"),
                            "emergency": item.get("emergency"),
                        })
                        break
        return results

if __name__ == "__main__":
    bot = HealthcareChatbot()
    bot.run()

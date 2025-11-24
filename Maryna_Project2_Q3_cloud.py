import streamlit as st

import tempfile
import fitz  
import docx2txt      
from bs4 import BeautifulSoup  
import re


# ---------- Small Helper: First Alphabetical Character ----------

def first_alpha_char(s):
    """Return the first alphabetical character in s, or None if not found."""
    for ch in s:
        if ch.isalpha():
            return ch
    return None


# ---------- Loading Text from Uploaded File ----------

def load_text_from_file(file):

    filename = file.name.lower()

    # Save uploaded file to a temporary path so other libraries can read it
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        temp_path = tmp.name

    # Plain text files
    if filename.endswith(".txt"):
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # PDF files
    if filename.endswith(".pdf"):
        text = ""
        pdf_document = fitz.open(temp_path)
        for page in pdf_document:
            text += page.get_text() + "\n"
        return text

    # Word .docx files
    if filename.endswith(".docx"):
        return docx2txt.process(temp_path)

    # HTML files
    if filename.endswith(".html") or filename.endswith(".htm"):
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        # get only visible text, separate blocks with newlines
        return soup.get_text(separator="\n")

    # Unsupported extension
    return ""


# ---------- Abbreviation Helper Constants ----------

# Words that should be ignored when building initials
PREPS = {
    "of", "for", "in", "on", "at", "by", "to", "from", "with",
    "about", "into", "over", "under", "between", "through",
    "the", "a", "an", "is", "are", "was", "were", "be", "being",
    "this", "that", "these", "those", "as", "than", "via"
}

# Common prefixes we want to treat specially when building initials
PREFIXES = [
    "auto", "multi", "micro", "macro",
    "electro", "hyper", "hypo",
    "inter", "intra",
    "ultra", "super", "sub", "trans"
]


# ---------- Building Initials from a Phrase ----------

def build_initials(words, has_amp, use_prefixes):
    """
    Build a list of initial letters from a phrase.
    """
    # Remove simple punctuation from word boundaries and drop empty tokens
    cleaned = [w.strip(".,;:()[]") for w in words if w.strip(".,;:()[]")]
    initials = []
    has_and = False

    for w in cleaned:
        word_lc = w.lower()

        # Special handling for the word "and"
        if word_lc == "and":
            if has_amp:
                has_and = True
            continue

        # Skip prepositions and function words entirely
        if word_lc in PREPS:
            continue

        # Replace hyphens with spaces → lowercase → split into parts
        normalized = w.replace("-", " ").replace("–", " ")
        parts = normalized.lower().split()

        for p in parts:

            # Try to detect known prefixes
            if use_prefixes:
                used_prefix = False
                for pref in PREFIXES:
                    if p.startswith(pref) and len(p) > len(pref):
                        # Initial from the prefix
                        initials.append(pref[0].upper())

                        # Initial from the root part
                        root = p[len(pref):]
                        ch = first_alpha_char(root)
                        if ch:
                            initials.append(ch.upper())

                        used_prefix = True
                        break

                if used_prefix:
                    continue

            # Default: first alphabetical character of p
            ch = first_alpha_char(p)
            if ch:
                initials.append(ch.upper())

    return initials, has_and


# ---------- Handling R&D-like Abbreviations (with &) ----------

def truncate_words_for_ampersand(words, letters_only):
    """
    For abbreviations with '&' and exactly two letters (like 'R&D'),
    we may want to truncate the phrase to only the words that correspond
    to these letters.
    """
    result = []
    collected = ""

    for w in words:
        core = w.strip(".,;:()[]")
        if not core:
            result.append(w)
            continue

        low = core.lower()
        # Keep prepositions and 'and' as-is, do not use them for matching
        if low in PREPS or low == "and":
            result.append(w)
            continue

        first_alpha = first_alpha_char(core)
        if first_alpha is None:
            result.append(w)
            continue

        # Compare collected initials with the target letters
        if len(collected) < len(letters_only) and first_alpha == letters_only[len(collected)]:
            result.append(w)
            collected += first_alpha
            if len(collected) == len(letters_only):
                # We matched all target letters; stop here
                break
        else:
            # As soon as a word does not match the next letter, stop
            break

    return result


# ---------- Matching a Phrase to an Abbreviation ----------

def phrase_matches_abbr(words, abbr):
    """
    Check if a sequence of words can reasonably correspond to a given abbreviation.
    """
    # Extract alphabetic characters only, e.g. "IPC4" → "IPC"
    letters_only_raw = "".join(c for c in abbr if c.isalpha())
    letters_only = letters_only_raw.upper()

    has_amp = "&" in abbr

    # Abbreviation variants: full form + singular without trailing S
    candidates = {letters_only}
    if len(letters_only) >= 3 and letters_only.endswith("S"):
        candidates.add(letters_only[:-1])

    def check(initials_str, has_and):
        # Basic match
        if initials_str in candidates and (not has_amp or has_and):
            return True

        # Special rule for 2-letter abbreviations with '&', like "R&D"
        if (
            has_amp
            and len(letters_only) == 2
            and initials_str.startswith(letters_only)
            and len(initials_str) > len(letters_only)
            and has_and
        ):
            return True

        return False

    # First attempt: without prefixes
    initials_base, has_and_base = build_initials(words, has_amp, use_prefixes=False)
    initials_str = "".join(initials_base)

    if check(initials_str, has_and_base):
        return True

    # If we already have too many initials, no need to try prefixes
    if len(initials_base) >= len(letters_only):
        return False

    # Second attempt: with prefixes
    initials_pref, has_and_pref = build_initials(words, has_amp, use_prefixes=True)
    initials_pref_str = "".join(initials_pref)

    if check(initials_pref_str, has_and_pref):
        return True

    return False


# ---------- Normalizing Capitalization of Long Phrases ----------

def normalize_phrase_caps(phrase: str) -> str:
    """
    Normalize capitalization of a long phrase for display.
    """
    lower_words = PREPS.union({"and", "or"})
    words = phrase.split()
    result = []

    for i, word in enumerate(words):
        is_first = (i == 0)
        is_last = (i == len(words) - 1)

        # Split word into non-word prefix, core, and non-word suffix.
        m_prefix = re.match(r'^\W+', word)
        m_suffix = re.search(r'\W+$', word)
        start = m_prefix.end() if m_prefix else 0
        end = m_suffix.start() if m_suffix else len(word)

        prefix = word[:start]
        core = word[start:end]
        suffix = word[end:]

        if not core:
            result.append(word)
            continue

        core_lower = core.lower()
        has_digit = any(ch.isdigit() for ch in core)

        if core.isupper() or has_digit:
            new_core = core
        elif core_lower in lower_words and not is_first:
            new_core = core_lower
        else:
            # Capitalize each hyphenated part separately.
            parts = re.split(r"([-–])", core)
            new_parts = []
            for j, p in enumerate(parts):
                if j % 2 == 1:
                    new_parts.append(p)
                else:
                    if p:
                        new_parts.append(p[0].upper() + p[1:].lower())
            new_core = "".join(new_parts)

        word_final = prefix + new_core + suffix

        # Remove trailing "'s" or "’s" from the last word
        if is_last:
            word_final = re.sub(r"[’']s(?=\W*$)", "", word_final)

        result.append(word_final)

    return " ".join(result)


# ---------- Main Abbreviation Extraction Function ----------

def extract_abbreviation_pairs(text: str):
    """
    Extract abbreviation → long-form pairs from the given text.
    """
    abbr_dict = {}

    # 0a. Digital Front: "4-digit IPC (IPC4)"
    pattern0a = r"\b(\d+-digit\s+([A-Z]{2,}))\s*\(([A-Z]{2,}\d+)\)"
    for m in re.finditer(pattern0a, text):
        phrase_raw = m.group(1)   # "4-digit IPC"
        abbr = m.group(3)         # "IPC4"
        if abbr not in abbr_dict:
            abbr_dict[abbr] = normalize_phrase_caps(phrase_raw)

    # 0b. Digital Back: "IPC4 (4-digit IPC)"
    pattern0b = r"\b([A-Z]{2,}\d+)\s*\(([^)]+)\)"
    for m in re.finditer(pattern0b, text):
        abbr = m.group(1)         # "IPC4"
        phrase_raw = m.group(2).strip(" ,.;:")  # "4-digit IPC"
        if abbr not in abbr_dict:
            abbr_dict[abbr] = normalize_phrase_caps(phrase_raw)

    # 1. Abbreviation first: "AF (Atrial Fibrillation)"
    pattern1 = r"\b([A-Z&]{2,}[sS]?)\s*\(([^)]+)\)"
    for m in re.finditer(pattern1, text):
        abbr = m.group(1)                     # "AF"
        phrase_raw = m.group(2).strip(" ,.;:")  # "Atrial Fibrillation"
        if abbr in abbr_dict:
            continue

        words = phrase_raw.split()
        if phrase_matches_abbr(words, abbr):
            abbr_dict[abbr] = normalize_phrase_caps(phrase_raw)

    # 2. Long form first: "Atrial Fibrillation (AF)"
    pattern2 = r"\(([A-Z&]{2,}[sS]?)[^)]*\)"
    for m in re.finditer(pattern2, text):
        abbr = m.group(1)
        if abbr in abbr_dict:
            continue

        # Look back up to 160 characters before '(' to find the candidate phrase
        start_paren = m.start()
        window = text[max(0, start_paren - 160):start_paren]

        # Normalize whitespace to single spaces
        window = re.sub(r"\s+", " ", window)

        # Take the last sentence-like fragment before '('
        fragment = re.split(r"[.!?;:]", window)[-1].strip()
        if not fragment:
            continue

        words = fragment.split()
        # Limit to the last 20 words to avoid very long phrases
        if len(words) > 20:
            words = words[-20:]

        best_phrase = None
        best_words = None

        # Try all suffixes of the candidate words and pick the one that matches
        for start in range(len(words)):
            cand = words[start:]
            if phrase_matches_abbr(cand, abbr):
                best_phrase = " ".join(cand).strip(" ,.;:")
                best_words = cand

        if best_phrase:
            letters_only = "".join(c for c in abbr if c.isalpha())
            # For abbreviations with '&' and two letters (e.g. "R&D"),
            # try to truncate the phrase to only the relevant words.
            if "&" in abbr and len(letters_only) == 2 and best_words is not None:
                best_phrase = " ".join(
                    truncate_words_for_ampersand(best_words, letters_only)
                ).strip(" ,.;:")
            abbr_dict[abbr] = normalize_phrase_caps(best_phrase)

    return abbr_dict


# ---------- HTML Rendering of Abbreviation List ----------

def render_abbreviations_html(abbr_dict):
    """
    Render abbreviation dictionary as a simple HTML unordered list.

    If no abbreviations are found, return a short message.
    """
    if not abbr_dict:
        return "<p>No abbreviations were found in the document.</p>"

    items = []
    for abbr in sorted(abbr_dict.keys()):
        full = abbr_dict[abbr].strip()
        items.append(
            f"<li><span style='color: blue; font-weight: bold;'>{abbr}</span>: {full}</li>"
        )

    return "<ul>\n" + "\n".join(items) + "\n</ul>"


# ---------- Streamlit UI (cloud version, no LLM) ----------

st.title("Input to AI")
st.write("You can extract abbreviations from an uploaded document.")


# File upload (only document, no question box)
uploaded_file = st.file_uploader(
    "Upload attachment:",
    type=["txt", "pdf", "docx", "html"]
)

# Main button – runs abbreviation extraction only
if st.button("Extract abbreviations"):
    # Load document text if file is provided
    if uploaded_file is not None:
        context_text = load_text_from_file(uploaded_file)
    else:
        context_text = ""

    # Abbreviation extraction
    if context_text.strip():
        abbr_dict = extract_abbreviation_pairs(context_text)
        st.subheader("Abbreviations found in the document:")
        html = render_abbreviations_html(abbr_dict)
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.write("No document was uploaded or no readable text was found, "
                 "so abbreviations cannot be extracted.")

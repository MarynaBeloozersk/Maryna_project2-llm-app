import streamlit as st

import tempfile
import fitz          # PyMuPDF: reading PDF text
import docx2txt      # reading .docx files
from bs4 import BeautifulSoup  # parsing HTML
import re


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

PREPS = {
    "of", "for", "in", "on", "at", "by", "to", "from", "with",
    "about", "into", "over", "under", "between", "through",
    "the", "a", "an", "is", "are", "was", "were", "be", "being",
    "this", "that", "these", "those", "as", "than", "via"
}

PREFIXES = [
    "auto", "multi", "micro", "macro",
    "electro", "hyper", "hypo",
    "inter", "intra",
    "ultra", "super", "sub", "trans"
]


# ---------- Building Initials from a Phrase ----------

def build_initials(words, has_amp, use_prefixes):
    
    # Remove simple punctuation from word boundaries and drop empty tokens
    cleaned = [w.strip(".,;:()[]") for w in words if w.strip(".,;:()[]")]
    initials = []
    has_and = False

    for w in cleaned:
        word_lc = w.lower()

        # Special handling: "and"
        if word_lc == "and":
            if has_amp:
                has_and = True
            continue

        # Skip prepositions
        if word_lc in PREPS:
            continue

        # Replace hyphens, make lowercase, split into parts
        normalized = w.replace("-", " ").replace("–", " ")
        parts = normalized.lower().split()   # <— simplified version

        for p in parts:

            # Try prefix-based logic
            if use_prefixes:
                used_prefix = False
                for pref in PREFIXES:
                    if p.startswith(pref) and len(p) > len(pref):
                        # Initial from prefix
                        initials.append(pref[0].upper())

                        # Initial from remaining root
                        root = p[len(pref):]
                        for ch in root:
                            if ch.isalpha():
                                initials.append(ch.upper())
                                break

                        used_prefix = True
                        break

                if used_prefix:
                    continue

            # Default: first alphabetical character
            for ch in p:
                if ch.isalpha():
                    initials.append(ch.upper())
                    break

    return initials, has_and


# ---------- Handling R&D-like Abbreviations ----------

def truncate_words_for_ampersand(words, letters_only):
    result = []
    collected = ""

    for w in words:
        core = w.strip(".,;:()[]")
        if not core:
            result.append(w)
            continue

        low = core.lower()

        if low in PREPS or low == "and":
            result.append(w)
            continue

        first_alpha = None
        for ch in core:
            if ch.isalpha():
                first_alpha = ch.upper()
                break

        if first_alpha is None:
            result.append(w)
            continue

        if len(collected) < len(letters_only) and first_alpha == letters_only[len(collected)]:
            result.append(w)
            collected += first_alpha
            if len(collected) == len(letters_only):
                break
        else:
            break

    return result


# ---------- Matching a Phrase to an Abbreviation ----------

def phrase_matches_abbr(words, abbr):

    letters_only_raw = "".join(c for c in abbr if c.isalpha())
    letters_only = letters_only_raw.upper()
    has_amp = "&" in abbr

    candidates = {letters_only}
    if len(letters_only) >= 3 and letters_only.endswith("S"):
        candidates.add(letters_only[:-1])

    def check(initials_str, has_and):
        if initials_str in candidates and (not has_amp or has_and):
            return True

        if (
            has_amp and
            len(letters_only) == 2 and
            initials_str.startswith(letters_only) and
            len(initials_str) > len(letters_only) and
            has_and
        ):
            return True

        return False

    initials_base, has_and_base = build_initials(words, has_amp, use_prefixes=False)
    initials_str = "".join(initials_base)

    if check(initials_str, has_and_base):
        return True

    if len(initials_base) >= len(letters_only):
        return False

    initials_pref, has_and_pref = build_initials(words, has_amp, use_prefixes=True)
    initials_pref_str = "".join(initials_pref)

    if check(initials_pref_str, has_and_pref):
        return True

    return False


# ---------- Normalize Long-Form Capitalization ----------

def normalize_phrase_caps(phrase: str) -> str:
    lower_words = PREPS.union({"and", "or"})
    words = phrase.split()
    result = []

    for i, word in enumerate(words):
        is_first = (i == 0)
        is_last = (i == len(words) - 1)

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

        if is_last:
            word_final = re.sub(r"[’']s(?=\W*$)", "", word_final)

        result.append(word_final)

    return " ".join(result)


# ---------- Extract Abbreviation Pairs ----------

def extract_abbreviation_pairs(text: str):

    abbr_dict = {}

    pattern0a = r"\b(\d+-digit\s+([A-Z]{2,}))\s*\(([A-Z]{2,}\d+)\)"
    for m in re.finditer(pattern0a, text):
        phrase_raw = m.group(1)
        abbr = m.group(3)
        if abbr not in abbr_dict:
            abbr_dict[abbr] = normalize_phrase_caps(phrase_raw)

    pattern0b = r"\b([A-Z]{2,}\d+)\s*\(([^)]+)\)"
    for m in re.finditer(pattern0b, text):
        abbr = m.group(1)
        phrase_raw = m.group(2).strip(" ,.;:")
        if abbr not in abbr_dict:
            abbr_dict[abbr] = normalize_phrase_caps(phrase_raw)

    pattern1 = r"\b([A-Z&]{2,}[sS]?)\s*\(([^)]+)\)"
    for m in re.finditer(pattern1, text):
        abbr = m.group(1)
        phrase_raw = m.group(2).strip(" ,.;:") 
        if abbr in abbr_dict:
            continue

        words = phrase_raw.split()
        if phrase_matches_abbr(words, abbr):
            abbr_dict[abbr] = normalize_phrase_caps(phrase_raw)

    pattern2 = r"\(([A-Z&]{2,}[sS]?)[^)]*\)"
    for m in re.finditer(pattern2, text):
        abbr = m.group(1)
        if abbr in abbr_dict:
            continue

        start_paren = m.start()
        window = text[max(0, start_paren - 160):start_paren]
        window = re.sub(r"\s+", " ", window)

        fragment = re.split(r"[.!?;:]", window)[-1].strip()
        if not fragment:
            continue

        words = fragment.split()
        if len(words) > 20:
            words = words[-20:]

        best_phrase = None
        best_words = None

        for start in range(len(words)):
            cand = words[start:]
            if phrase_matches_abbr(cand, abbr):
                best_phrase = " ".join(cand).strip(" ,.;:")
                best_words = cand

        if best_phrase:
            letters_only = "".join(c for c in abbr if c.isalpha())
            if "&" in abbr and len(letters_only) == 2 and best_words is not None:
                best_phrase = " ".join(
                    truncate_words_for_ampersand(best_words, letters_only)
                ).strip(" ,.;:")
            abbr_dict[abbr] = normalize_phrase_caps(best_phrase)

    return abbr_dict


# ---------- Render HTML ----------

def render_abbreviations_html(abbr_dict):

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

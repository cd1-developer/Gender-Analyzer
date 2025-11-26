import re

# --- Gender detection rules (LOCAL) ---
# High confidence keywords (titles, clear gender terms)
male_keywords_high = ["mr", "sir", "gentleman", "man", "male", "boy", "king", "prince"]
female_keywords_high = ["mrs", "ms", "miss", "madam", "lady", "female", "girl", "queen", "princess"]

# Lower confidence name parts/endings
male_endings = [
    "ad", "ald", "an", "ard", "as", "bart", "bert", "brook", "croft", "dal",
    "den", "don", "el", "er", "es", "field", "ford", "hard", "holt", "ic",
    "ick", "ik", "in", "kell", "man", "mart", "men", "mer", "mond", "mont",
    "ner", "o", "os", "rell", "ric", "rick", "ridge", "ron", "sen", "smith",
    "son", "stone", "ter", "tin", "ton", "us", "vale", "ward", "well",
    "wood", "wright", "yor"
]

female_endings = [
    "a", "ayah", "bella", "beth", "betha", "cia", "eisha", "ela", "ella", "elle",
    "en", "era", "etta", "ette", "et", "ia", "iah", "ina", "ine", "ira", "ita",
    "ka", "lea", "lena", "lia", "line", "lina", "lora", "lyn", "lynne", "lynn",
    "mara", "mera", "na", "nia", "nora", "ona", "ora", "ota", "ria", "rose",
    "sea", "sia", "ta", "tia", "ula", "ura", "via", "yla"
]


# Prepositions/Connectors to ignore in analysis
ignore_words = ["and", "the", "a", "of", "for", "with", "at", "by", "in", "to", "from", "user", "name"]


def apply_gender_guess(fullname, username,male_female_keywords) -> dict:
    """
    Helper function to apply combined_guess to a DataFrame row (Series),
    using the aggressively cleaned name column.
    """
    # Use the pre-cleaned column for analysis
    
    gender, confidence = combined_guess(fullname, username,male_female_keywords)

    return {'username':username, 'full_name':fullname, 'gender': gender, 'confidence': confidence}



# -------------------------------------------------------------------------
# --- REVISED combined_guess FUNCTION (FULL NAME PRIORITY, MAX CONFIDENCE TRACKING) ---
# -------------------------------------------------------------------------
def combined_guess(fullname_processed, username_original,male_female_keywords):
    """
    Combines analysis, prioritizing the aggressively cleaned full name first, 
    then falling back to the original username, always returning the highest confidence result.
    """
    
    # Initialize best guess with the Ambiguous default (conf=50)
    best_gender = "Ambiguous"
    max_conf = 50 

    # 1. Check Full Name (Primary Check)
    gender_fn, conf_fn = analyze_name(fullname_processed,male_female_keywords)
    if conf_fn > max_conf:
        best_gender, max_conf = gender_fn, conf_fn
    
    # 2. Check Full Username (Fallback Check 1)
    gender_un, conf_un = analyze_name(username_original,male_female_keywords)
    # Apply a slight penalty if it's used only as a fallback
    conf_un_adjusted = conf_un - 5 
    if conf_un_adjusted > max_conf: 
        best_gender, max_conf = gender_un, conf_un_adjusted

    # 3. Check the first part of the cleaned username (Fallback Check 2)
    cleaned_un = clean_name(username_original)
    first_name_guess = cleaned_un.split()[0] if cleaned_un else ""

    if first_name_guess:
        # Re-analyze ONLY the first word to force a dictionary/ending match
        gender_first, conf_first = analyze_name(first_name_guess,male_female_keywords)
        if conf_first > 50:
             # Ensure this first-word guess always gets a floor confidence of 60 if found
            conf_first_adjusted = max(conf_first, 60)
            if conf_first_adjusted > max_conf:
                best_gender, max_conf = gender_first, conf_first_adjusted
    
    return best_gender, max_conf

def analyze_name(name,male_female_keywords):
    """Core logic to guess gender based on keywords, DICTIONARY LOOKUP, and endings."""
    clean_n = clean_name(name)
    if not clean_n:
        return "Ambiguous", 0

    name_words = clean_n.split()
    if not name_words:
        return "Ambiguous", 0
    
    first_word = name_words[0]
    second_word = name_words[1] if len(name_words) > 1 else None

    # 1. High-Confidence Keyword Check (e.g., 'mr smith') - CONFIDENCE 99
    for kw in male_keywords_high:
        if kw in name_words:
            return "Male", 99
    for kw in female_keywords_high:
        if kw in name_words:
            return "Female", 99

    # 2A. Dictionary Lookup on First Word (Primary source of truth - USA only) - CONFIDENCE 95
    if first_word in male_female_keywords:
        gender = male_female_keywords[first_word]
        return gender, 95
            
    # 2B. Dictionary Lookup on Second Word (USA only) - CONFIDENCE 90 
    if second_word and second_word in male_female_keywords:
        gender = male_female_keywords[second_word]
        return gender, 90

    # 3. Ending Pattern Check (Focus on the first word) - CONFIDENCE 91-93 (BOOSTED)
    for end in male_endings:
        if first_word.endswith(end) and len(first_word) > 2:
            return "Male", 91 # Elevated from 85
    for end in female_endings:
        if first_word.endswith(end) and len(first_word) > 2:
            return "Female", 93 # Elevated from 87
            
    # 4. Fallback Ending Check (Last word) - CONFIDENCE 80-82 (BOOSTED)
    last_word = name_words[-1]
    if last_word != first_word and len(last_word) > 2: 
        for end in male_endings:
            if last_word.endswith(end):
                return "Male", 80 # Elevated from 70
        for end in female_endings:
            if last_word.endswith(end):
                return "Female", 82 # Elevated from 72

    return "Ambiguous", 50 # Base ambiguous confidence




# --- FUNCTION FOR AGGRESSIVE FULL NAME CLEANING ---
def aggressively_clean_fullname(name):
    """Removes common titles, suffixes, and single initials that can confuse the guesser."""
    name = str(name).lower().strip()
    if not name:
        return ""
        
    # 1. Remove common titles/suffixes (e.g., dr, prof, jr, sr, ii, iii)
    name = re.sub(r'\b(mr|mrs|ms|dr|prof|jr|sr|iii?|esq)\b', ' ', name)
    
    # 2. Remove single initials (like "A. B. Smith" -> "Smith")
    name = re.sub(r'\b[a-z]\.\s*', ' ', name)
    name = re.sub(r'\b[a-z]\b', ' ', name)
    
    # 3. Clean up extra spaces left by the replacements
    return re.sub(r'\s+', ' ', name).strip()
# --------------------------------------------------

def clean_name(name):
    """Clean and normalize the name/username for analysis (used mainly for username)."""
    name = str(name).lower().strip()
    if not name:
        return ""
    # Remove common username separators and numbers (e.g., john.doe123 -> john doe)
    # Aggressively replace common non-alphanumeric separators with spaces
    name = re.sub(r'[^a-z]+', ' ', name)
    name = re.sub(r'\d+', ' ', name)
    # Remove single letters and common prepositions/words
    name_parts = [word for word in name.split() if len(word) > 1 and word not in ignore_words]
    return " ".join(name_parts)

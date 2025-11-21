import re

# --- Gender detection rules (LOCAL) ---
# High confidence keywords (titles, clear gender terms)
male_keywords_high = ["mr", "sir", "gentleman", "man", "male", "boy", "king", "prince"]
female_keywords_high = ["mrs", "ms", "miss", "madam", "lady", "female", "girl", "queen", "princess"]

# Lower confidence name parts/endings
male_endings = ["o", "as", "os", "an", "ik", "us", "er", "es", "el", "ad", "in"]
female_endings = ["a", "ia", "na", "ta", "ine", "elle", "ka", "et", "en"]

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



# --- REVISED combined_guess FUNCTION (HANDLES PRIORITY LOGIC - USERNAME FIRST) ---
def combined_guess(fullname_processed, username_original,male_female_keywords):
    """
    Combines analysis, prioritizing the original username first, 
    then falling back to the aggressively cleaned full name.
    """
    
    # 1. Try the full Username (Check 1 - NEW PRIMARY CHECK)
    gender_un, conf_un = analyze_name(username_original,male_female_keywords)
    if conf_un > 55:
        # If the username provides a good guess, use it
        return gender_un, conf_un
    
    # 2. Try the first part of the cleaned username (Check 2 - Secondary Username check)
    cleaned_un = clean_name(username_original)
    first_name_guess = cleaned_un.split()[0] if cleaned_un else ""

    if first_name_guess:
        # Re-analyze ONLY the first word to force a dictionary/ending match
        gender_first, conf_first = analyze_name(first_name_guess,male_female_keywords)
        
        # Accept this guess if it's better than pure Ambiguous (conf_first > 50)
        if conf_first > 50 and conf_first > conf_un: # Only take it if it improves the guess
            # Assign a slightly elevated confidence for the first word match
            return gender_first, max(conf_first, 60) # Guarantee a reasonable confidence if found

    # 3. Fallback to Processed Full Name (Check 3 - NEW FALLBACK)
    gender_fn, conf_fn = analyze_name(fullname_processed,male_female_keywords)
    if conf_fn > 50:
        # Reduce confidence for the fallback check (Full Name) to reflect lower priority
        return gender_fn, conf_fn - 5

    # 4. Final Fallback (Lowest confidence result)
    return gender_fn, conf_fn


# --- CORE analyze_name FUNCTION (Updated with deeper check) ---
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

    # 2A. Dictionary Lookup on First Word (Primary source of truth) - CONFIDENCE 95
    if first_word in male_female_keywords:
        gender = male_female_keywords[first_word]
        return gender, 95
            
    # 2B. Dictionary Lookup on Second Word - CONFIDENCE 90 
    if second_word and second_word in male_female_keywords:
        gender = male_female_keywords[second_word]
        return gender, 90

    # 3. Ending Pattern Check (Focus on the first word) - CONFIDENCE 85-87
    for end in male_endings:
        if first_word.endswith(end) and len(first_word) > 2:
            return "Male", 85
    for end in female_endings:
        if first_word.endswith(end) and len(first_word) > 2:
            return "Female", 87
            
    # 4. Fallback Ending Check (Last word) - CONFIDENCE 70-72
    last_word = name_words[-1]
    if last_word != first_word and len(last_word) > 2: 
        for end in male_endings:
            if last_word.endswith(end):
                return "Male", 70
        for end in female_endings:
            if last_word.endswith(end):
                return "Female", 72

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

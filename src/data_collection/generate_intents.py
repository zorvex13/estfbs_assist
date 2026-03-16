import json
import re
import os

def generate_draft_intents(input_file, output_file):
    print(f"Reading raw data from {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}. Make sure you are in the right folder.")
        return

    # Split the raw text into smaller chunks (rough sentence/paragraph splitting)
    # This helps us grab specific rules instead of whole pages
    chunks = re.split(r'(?<=[.!?])\s+', raw_text)

    # Define our rules: If we see a KEYWORD in the text, generate these BILINGUAL PATTERNS
# Define our rules: If we see a KEYWORD in the text, generate these BILINGUAL PATTERNS
    extraction_rules = {
        # --- 1. ABSENCES ---
        "absence": {
            "tag": "reglement_absence",
            "patterns": [
                "Quelles sont les règles d'absence ?",
                "Comment justifier une absence ?",
                "شنو القوانين ديال الغياب؟",
                "wach n9der njustifier absence",
                "ch7al mn nhar bach njustifier",
                "j'étais malade"
            ]
        },
        "00/20": {
            "tag": "sanction_absence_examen",
            "patterns": [
                "Est-ce que j'aurai 0 si je suis absent à l'examen ?",
                "Que se passe-t-il si je rate un DS ?",
                "شنو يوقع يلا غبت ف الامتحان؟",
                "wach radi nakhod 0 f ds"
            ]
        },
        
        # --- 2. VALIDATION DES MODULES ---
        "valider": {
            "tag": "validation_module",
            "patterns": [
                "Comment valider un module ?",
                "C'est quoi la note pour valider ?",
                "شحال خصني نجيب باش نفاليدي الموديل؟",
                "kifach nvalider semestre",
                "la note éliminatoire"
            ]
        },
        "compensation": {
            "tag": "compensation_semestre",
            "patterns": [
                "Comment fonctionne la compensation entre les semestres ?",
                "Est-ce que je peux compenser un module ?",
                "wach kayn compensation f EST ?",
                "kifach ncompenser les notes"
            ]
        },
        "rattrapage": {
            "tag": "session_rattrapage",
            "patterns": [
                "Qui a le droit de passer le rattrapage ?",
                "Comment passer la session de rattrapage ?",
                "fo9ach rattrapage",
                "chkoune li kaydwz rattrapage"
            ]
        },

        # --- 3. STAGES ET PFE ---
        "stage": {
            "tag": "reglement_stage_pfe",
            "patterns": [
                "Quelles sont les règles pour le stage de fin d'études ?",
                "Comment valider le PFE ?",
                "fo9ach nswwbo rapport de stage",
                "wach stage darouri",
                "معلومات على التدريب PFE",
                "soutenance de stage"
            ]
        },

        # --- 4. REGLEMENT INTERIEUR (Général) ---
        "comportement": {
            "tag": "reglement_comportement",
            "patterns": [
                "C'est quoi le règlement intérieur ?",
                "Quelles sont les sanctions disciplinaires ?",
                "قانون المدرسة",
                "chnou hya l9awanin d l'ecole",
                "conseil de discipline"
            ]
        },
        "tél": {
            "tag": "contact_administration",
            "patterns": [
                "Quel est le numéro de l'école ?",
                "Comment contacter l'administration ?",
                "رقم هاتف الإدارة",
                "numéro de téléphone EST",
                "fin jat l'administration"
            ]
        }
    }

    intents = {"intents": []}
    used_tags = set()

    print("Extracting rules and generating bilingual intents...")
    
    for chunk in chunks:
        chunk_clean = chunk.strip().replace('\n', ' ')
        
        # Skip chunks that are too short to be useful
        if len(chunk_clean) < 20:
            continue

        for keyword, data in extraction_rules.items():
            # If the keyword is found in this chunk of text, and we haven't already created this tag
            if re.search(r'\b' + re.escape(keyword) + r'\b', chunk_clean, re.IGNORECASE) and data["tag"] not in used_tags:
                
                new_intent = {
                    "tag": data["tag"],
                    "patterns": data["patterns"],
                    "responses": [chunk_clean] # The actual rule extracted from your PDF
                }
                intents["intents"].append(new_intent)
                used_tags.add(data["tag"])
                break # Move to the next chunk once we find a match

    # Add a default greeting intent just to round it out
    intents["intents"].append({
        "tag": "salutation",
        "patterns": ["salam", "bonjour", "hello", "wach", "السلام"],
        "responses": ["Bonjour! Je suis le chatbot de l'EST FBS. Posez-moi vos questions sur le règlement ou les études."]
    })

    # Save to the processed folder
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(intents, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccess! Generated {len(intents['intents'])} intents.")
    print(f"Draft saved to: {output_file}")

# Execute the function
input_path = "est_fbs_chatbot/data/raw/est_fbs_data.txt"
output_path = "est_fbs_chatbot/data/processed/intents.json"
generate_draft_intents(input_path, output_path)
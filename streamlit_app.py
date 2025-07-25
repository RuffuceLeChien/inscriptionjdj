import streamlit as st
import pandas as pd
import json
import hashlib
import random
import string
from datetime import datetime, date
import re

# Configuration de la page
st.set_page_config(
    page_title="Inscription JdJ",
    layout="wide"
)

# Configuration des fichiers de données
REGISTRATIONS_FILE = "registrations.json"
CONFIRMED_FILE = "confirmed.json"
MODERATORS_FILE = "moderators.json"

# Mot de passe par défaut pour les modérateurs (à changer en production)
DEFAULT_MODERATOR_PASSWORD = "admin123"

def load_data(filename):
    """Charge les données depuis un fichier JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data, filename):
    """Sauvegarde les données dans un fichier JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def validate_email(email):
    """Valide le format de l'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_captcha():
    """Génère un captcha simple"""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        result = num1 + num2
    elif operation == '-':
        result = num1 - num2
    else:  # multiplication
        result = num1 * num2
    
    return f"{num1} {operation} {num2}", result

def hash_password(password):
    """Hash un mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_session_state():
    """Initialise les variables de session"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'captcha_question' not in st.session_state:
        st.session_state.captcha_question, st.session_state.captcha_answer = generate_captcha()
    if 'page' not in st.session_state:
        st.session_state.page = 'inscription'

def registration_page():
    """Page d'inscription pour les participants"""
    st.title("🎉 Inscription à l'Événement")
    st.markdown("---")
    
    with st.form("inscription_form"):
        st.header("📝 Informations personnelles")
        
        # Champs du formulaire
        email = st.text_input("📧 Adresse email *", placeholder="votre.email@exemple.com")
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("👤 Nom *", placeholder="Dupont")
        with col2:
            prenom = st.text_input("👤 Prénom *", placeholder="Jean")
        
        date_naissance = st.date_input(
            "📅 Date de naissance *",
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )
        
        # Captcha
        st.subheader("🤖 Vérification anti-robot")
        st.write(f"Résolvez cette opération : **{st.session_state.captcha_question}**")
        captcha_response = st.number_input("Votre réponse", min_value=-100, max_value=100, value=0)
        
        submitted = st.form_submit_button("✅ S'inscrire", type="primary", use_container_width=True)
        
        if submitted:
            # Validation des champs
            errors = []
            
            if not email or not validate_email(email):
                errors.append("❌ Adresse email invalide")
            if not nom.strip():
                errors.append("❌ Le nom est obligatoire")
            if not prenom.strip():
                errors.append("❌ Le prénom est obligatoire")
            if captcha_response != st.session_state.captcha_answer:
                errors.append("❌ Réponse incorrecte au captcha")
            
            if errors:
                for error in errors:
                    st.error(error)
                # Générer un nouveau captcha
                st.session_state.captcha_question, st.session_state.captcha_answer = generate_captcha()
                st.rerun()
            else:
                # Sauvegarder l'inscription
                registrations = load_data(REGISTRATIONS_FILE)
                current_year = str(datetime.now().year)
                
                if current_year not in registrations:
                    registrations[current_year] = []
                
                # Vérifier si l'email existe déjà
                email_exists = any(reg['email'] == email for reg in registrations[current_year])
                
                if email_exists:
                    st.error("❌ Cette adresse email est déjà enregistrée")
                else:
                    new_registration = {
                        'id': len(registrations[current_year]) + 1,
                        'email': email,
                        'nom': nom.strip(),
                        'prenom': prenom.strip(),
                        'date_naissance': str(date_naissance),
                        'date_inscription': str(datetime.now()),
                        'confirmed': False
                    }
                    
                    registrations[current_year].append(new_registration)
                    save_data(registrations, REGISTRATIONS_FILE)
                    
                    st.success("🎉 Inscription réussie ! Votre demande sera examinée par les modérateurs.")
                    
                    # Générer un nouveau captcha pour la prochaine inscription
                    st.session_state.captcha_question, st.session_state.captcha_answer = generate_captcha()

def moderator_login():
    """Page de connexion pour les modérateurs"""
    st.title("🔐 Connexion Modérateur")
    
    with st.form("login_form"):
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
        
        if submit:
            if hash_password(password) == hash_password(DEFAULT_MODERATOR_PASSWORD):
                st.session_state.logged_in = True
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Mot de passe incorrect")

def moderator_dashboard():
    """Tableau de bord pour les modérateurs"""
    st.title("👨‍💼 Tableau de bord - Modérateurs")
    
    # Menu de navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Inscriptions en attente", 
        "✅ Inscriptions confirmées", 
        "📊 Historique", 
        "📧 Export emails"
    ])
    
    registrations = load_data(REGISTRATIONS_FILE)
    current_year = str(datetime.now().year)
    
    with tab1:
        st.header("📋 Inscriptions en attente de validation")
        
        if current_year not in registrations or not registrations[current_year]:
            st.info("Aucune inscription en attente pour cette année.")
        else:
            pending = [reg for reg in registrations[current_year] if not reg['confirmed']]
            
            if not pending:
                st.info("Aucune inscription en attente de validation.")
            else:
                for reg in pending:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**{reg['prenom']} {reg['nom']}**")
                            st.write(f"📧 {reg['email']}")
                            st.write(f"📅 Né(e) le {reg['date_naissance']}")
                            st.write(f"🕐 Inscrit le {reg['date_inscription'][:10]}")
                        
                        with col2:
                            if st.button("✅ Confirmer", key=f"confirm_{reg['id']}"):
                                # Confirmer l'inscription
                                for i, r in enumerate(registrations[current_year]):
                                    if r['id'] == reg['id']:
                                        registrations[current_year][i]['confirmed'] = True
                                        break
                                save_data(registrations, REGISTRATIONS_FILE)
                                st.success("Inscription confirmée !")
                                st.rerun()
                        
                        with col3:
                            if st.button("❌ Supprimer", key=f"delete_{reg['id']}"):
                                # Supprimer l'inscription
                                registrations[current_year] = [r for r in registrations[current_year] if r['id'] != reg['id']]
                                save_data(registrations, REGISTRATIONS_FILE)
                                st.success("Inscription supprimée !")
                                st.rerun()
                        
                        st.markdown("---")
    
    with tab2:
        st.header("✅ Inscriptions confirmées")
        
        if current_year not in registrations or not registrations[current_year]:
            st.info("Aucune inscription confirmée pour cette année.")
        else:
            confirmed = [reg for reg in registrations[current_year] if reg['confirmed']]
            
            if not confirmed:
                st.info("Aucune inscription confirmée pour cette année.")
            else:
                st.success(f"**{len(confirmed)} inscription(s) confirmée(s) pour {current_year}**")
                
                # Affichage sous forme de tableau
                df = pd.DataFrame(confirmed)
                df = df[['prenom', 'nom', 'email', 'date_naissance', 'date_inscription']]
                df.columns = ['Prénom', 'Nom', 'Email', 'Date de naissance', 'Date d\'inscription']
                st.dataframe(df, use_container_width=True)
    
    with tab3:
        st.header("📊 Historique des années précédentes")
        
        if not registrations:
            st.info("Aucun historique disponible.")
        else:
            years = sorted(registrations.keys(), reverse=True)
            
            for year in years:
                if year != current_year:
                    confirmed_count = len([reg for reg in registrations[year] if reg['confirmed']])
                    total_count = len(registrations[year])
                    
                    with st.expander(f"📅 Année {year} - {confirmed_count}/{total_count} confirmées"):
                        confirmed_year = [reg for reg in registrations[year] if reg['confirmed']]
                        
                        if confirmed_year:
                            df = pd.DataFrame(confirmed_year)
                            df = df[['prenom', 'nom', 'email', 'date_naissance', 'date_inscription']]
                            df.columns = ['Prénom', 'Nom', 'Email', 'Date de naissance', 'Date d\'inscription']
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("Aucune inscription confirmée pour cette année.")
    
    with tab4:
        st.header("📧 Export des adresses email")
        
        # Sélection de l'année
        available_years = list(registrations.keys()) if registrations else []
        
        if not available_years:
            st.info("Aucune donnée disponible pour l'export.")
        else:
            selected_year = st.selectbox("Choisir l'année", available_years, index=0)
            
            if selected_year in registrations:
                confirmed = [reg for reg in registrations[selected_year] if reg['confirmed']]
                
                if confirmed:
                    emails = [reg['email'] for reg in confirmed]
                    emails_text = "; ".join(emails)
                    
                    st.success(f"**{len(emails)} adresse(s) email confirmée(s) pour {selected_year}**")
                    
                    # Zone de texte avec les emails
                    st.text_area(
                        "Adresses email (séparées par des points-virgules)",
                        value=emails_text,
                        height=150
                    )
                    
                    # Bouton de copie (information)
                    st.info("💡 Vous pouvez sélectionner le texte ci-dessus et le copier avec Ctrl+C")
                    
                    # Download button
                    st.download_button(
                        label="💾 Télécharger la liste des emails",
                        data=emails_text,
                        file_name=f"emails_{selected_year}.txt",
                        mime="text/plain"
                    )
                else:
                    st.info(f"Aucune inscription confirmée pour {selected_year}.")

def main():
    """Fonction principale"""
    init_session_state()
    
    # Sidebar pour la navigation
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("🎉 Inscription", use_container_width=True):
            st.session_state.page = 'inscription'
            st.rerun()
        
        if st.button("🔐 Modérateurs", use_container_width=True):
            st.session_state.page = 'moderator'
            st.rerun()
        
        if st.session_state.logged_in:
            st.success("✅ Connecté en tant que modérateur")
            if st.button("🚪 Se déconnecter", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.page = 'inscription'
                st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        st.markdown("**Année actuelle :** " + str(datetime.now().year))
        
        # Statistiques rapides
        registrations = load_data(REGISTRATIONS_FILE)
        current_year = str(datetime.now().year)
        
        if current_year in registrations:
            total = len(registrations[current_year])
            confirmed = len([reg for reg in registrations[current_year] if reg['confirmed']])
            pending = total - confirmed
            
            st.markdown(f"**Inscriptions {current_year} :**")
            st.markdown(f"- Total : {total}")
            st.markdown(f"- Confirmées : {confirmed}")
            st.markdown(f"- En attente : {pending}")
    
    # Affichage de la page appropriée
    if st.session_state.page == 'inscription':
        registration_page()
    elif st.session_state.page == 'moderator':
        if not st.session_state.logged_in:
            moderator_login()
        else:
            moderator_dashboard()

if __name__ == "__main__":
    main()
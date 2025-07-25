import streamlit as st
import pandas as pd
import json
import hashlib
import random
import string
from datetime import datetime, date
import re
import os
import base64
from PIL import Image
import io

# Configuration de la page
st.set_page_config(
    page_title="Inscription JdJ",
    layout="wide"
)

# Configuration des fichiers de données
REGISTRATIONS_FILE = "registrations.json"
CONFIRMED_FILE = "confirmed.json"
MODERATORS_FILE = "moderators.json"
IMAGE_CONFIG_FILE = "image_config.json"
CONTENT_CONFIG_FILE = "content_config.json"
IMAGES_FOLDER = "uploaded_images"

# Mot de passe par défaut pour les modérateurs (à changer en production)
DEFAULT_MODERATOR_PASSWORD = "admin123"

# Créer le dossier pour les images uploadées s'il n'existe pas
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

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

def load_image_config():
    """Charge la configuration de l'image"""
    try:
        with open(IMAGE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"image_type": "none", "image_url": "", "image_path": "", "image_caption": ""}

def save_image_config(config):
    """Sauvegarde la configuration de l'image"""
    with open(IMAGE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_content_config():
    """Charge la configuration du contenu modulable"""
    try:
        with open(CONTENT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"elements": []}

def save_content_config(config):
    """Sauvegarde la configuration du contenu modulable"""
    with open(CONTENT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def save_uploaded_image(uploaded_file):
    """Sauvegarde une image uploadée et retourne le chemin"""
    if uploaded_file is not None:
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        filepath = os.path.join(IMAGES_FOLDER, filename)
        
        # Ouvrir et redimensionner l'image si nécessaire
        try:
            image = Image.open(uploaded_file)
            
            # Redimensionner l'image si elle est trop grande
            max_size = (800, 600)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convertir en RGB si nécessaire (pour éviter les problèmes avec PNG)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # Sauvegarder l'image
            image.save(filepath, "JPEG", quality=85)
            return filepath
            
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde de l'image : {e}")
            return None
    return None

def display_custom_content():
    """Affiche le contenu personnalisé configuré par les administrateurs"""
    content_config = load_content_config()
    
    if not content_config.get("elements"):
        return
    
    for element in content_config["elements"]:
        element_type = element.get("type")
        
        if element_type == "text":
            if element.get("style") == "header":
                st.header(element.get("content", ""))
            elif element.get("style") == "subheader":
                st.subheader(element.get("content", ""))
            elif element.get("style") == "markdown":
                st.markdown(element.get("content", ""))
            else:  # normal text
                st.write(element.get("content", ""))
                
        elif element_type == "image":
            if element.get("image_type") == "url" and element.get("image_url"):
                try:
                    st.image(
                        element["image_url"], 
                        caption=element.get("caption", ""),
                        width=element.get("width")
                    )
                except:
                    st.error("Erreur lors du chargement de l'image")
            elif element.get("image_type") == "local" and element.get("image_path"):
                try:
                    if os.path.exists(element["image_path"]):
                        st.image(
                            element["image_path"], 
                            caption=element.get("caption", ""),
                            width=element.get("width")
                        )
                    else:
                        st.error("Image locale introuvable")
                except:
                    st.error("Erreur lors du chargement de l'image locale")
                    
def display_image_from_config():
    """Affiche l'image selon la configuration"""
    image_config = load_image_config()
    
    if image_config.get("image_type") == "url" and image_config.get("image_url"):
        try:
            st.image(image_config["image_url"], caption=image_config.get("image_caption", ""), use_container_width=True)
            return True
        except Exception as e:
            st.error("Erreur lors du chargement de l'image depuis l'URL")
            return False
    elif image_config.get("image_type") == "local" and image_config.get("image_path"):
        try:
            if os.path.exists(image_config["image_path"]):
                st.image(image_config["image_path"], caption=image_config.get("image_caption", ""), use_container_width=True)
                return True
            else:
                st.error("Le fichier image local n'existe plus")
                return False
        except Exception as e:
            st.error("Erreur lors du chargement de l'image locale")
            return False
    else:
        st.info("Aucune image configurée")
        return False

def home_page():
    """Page d'accueil"""
    st.title("Journée de la jeunesse")
    st.markdown("---")
    
    # Configuration en deux colonnes principales
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Affichage du contenu personnalisé dans la colonne de gauche
        display_custom_content()
        
        # Espace au-dessus du bouton
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bouton d'inscription
        if st.button("S'inscrire à l'événement", type="primary", use_container_width=True):
            st.session_state.page = 'inscription'
            st.rerun()
    
    with col2:
        # Affichage de l'image principale dans la colonne de droite
        display_image_from_config()

def init_session_state():
    """Initialise les variables de session"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'captcha_question' not in st.session_state:
        st.session_state.captcha_question, st.session_state.captcha_answer = generate_captcha()
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

def registration_page():
    """Page d'inscription pour les participants"""
    st.title("Inscription JdJ")
    st.markdown("---")
    
    with st.form("inscription_form"):
        st.header("Informations personnelles")
        
        # Champs du formulaire
        email = st.text_input("Adresse email *", placeholder="votre.email@exemple.com")
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("Nom *", placeholder="Dupont")
        with col2:
            prenom = st.text_input("Prénom *", placeholder="Jean")
        
        date_naissance = st.date_input(
            "Date de naissance *",
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )
        
        # Captcha
        st.subheader("Vérification anti-robot")
        st.write(f"Résolvez cette opération : **{st.session_state.captcha_question}**")
        captcha_response = st.number_input("Votre réponse", min_value=-100, max_value=100, value=0)
        
        submitted = st.form_submit_button("S'inscrire", type="primary", use_container_width=True)
        
        if submitted:
            # Validation des champs
            errors = []
            
            if not email or not validate_email(email):
                errors.append("Adresse email invalide")
            if not nom.strip():
                errors.append("Le nom est obligatoire")
            if not prenom.strip():
                errors.append("Le prénom est obligatoire")
            if captcha_response != st.session_state.captcha_answer:
                errors.append("Réponse incorrecte au captcha")
            
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
                    st.error("Cette adresse email est déjà enregistrée")
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
                    
                    st.success("Inscription réussie ! Votre demande sera examinée par les modérateurs.")
                    
                    # Générer un nouveau captcha pour la prochaine inscription
                    st.session_state.captcha_question, st.session_state.captcha_answer = generate_captcha()

def moderator_login():
    """Page de connexion pour les modérateurs"""
    st.title("Connexion Modérateur")
    
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
    st.title("Tableau de bord - Modérateurs")
    
    # Menu de navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Inscriptions en attente", 
        "Inscriptions confirmées", 
        "Historique", 
        "Export emails",
        "Gestion image",
        "Contenu personnalisé"
    ])
    
    registrations = load_data(REGISTRATIONS_FILE)
    current_year = str(datetime.now().year)
    
    with tab1:
        st.header("Inscriptions en attente de validation")
        
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
                            st.write(f"Email: {reg['email']}")
                            st.write(f"Né(e) le {reg['date_naissance']}")
                            st.write(f"Inscrit le {reg['date_inscription'][:10]}")
                        
                        with col2:
                            if st.button("Confirmer", key=f"confirm_{reg['id']}"):
                                # Confirmer l'inscription
                                for i, r in enumerate(registrations[current_year]):
                                    if r['id'] == reg['id']:
                                        registrations[current_year][i]['confirmed'] = True
                                        break
                                save_data(registrations, REGISTRATIONS_FILE)
                                st.success("Inscription confirmée !")
                                st.rerun()
                        
                        with col3:
                            if st.button("Supprimer", key=f"delete_{reg['id']}"):
                                # Supprimer l'inscription
                                registrations[current_year] = [r for r in registrations[current_year] if r['id'] != reg['id']]
                                save_data(registrations, REGISTRATIONS_FILE)
                                st.success("Inscription supprimée !")
                                st.rerun()
                        
                        st.markdown("---")
    
    with tab2:
        st.header("Inscriptions confirmées")
        
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
        st.header("Historique des années précédentes")
        
        if not registrations:
            st.info("Aucun historique disponible.")
        else:
            years = sorted(registrations.keys(), reverse=True)
            
            for year in years:
                if year != current_year:
                    confirmed_count = len([reg for reg in registrations[year] if reg['confirmed']])
                    total_count = len(registrations[year])
                    
                    with st.expander(f"Année {year} - {confirmed_count}/{total_count} confirmées"):
                        confirmed_year = [reg for reg in registrations[year] if reg['confirmed']]
                        
                        if confirmed_year:
                            df = pd.DataFrame(confirmed_year)
                            df = df[['prenom', 'nom', 'email', 'date_naissance', 'date_inscription']]
                            df.columns = ['Prénom', 'Nom', 'Email', 'Date de naissance', 'Date d\'inscription']
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("Aucune inscription confirmée pour cette année.")
    
    with tab4:
        st.header("Export des adresses email")
        
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
                    st.info("Vous pouvez sélectionner le texte ci-dessus et le copier avec Ctrl+C")
                    
                    # Download button
                    st.download_button(
                        label="Télécharger la liste des emails",
                        data=emails_text,
                        file_name=f"emails_{selected_year}.txt",
                        mime="text/plain"
                    )
                else:
                    st.info(f"Aucune inscription confirmée pour {selected_year}.")
    
    with tab5:
        st.header("Gestion de l'image d'accueil")
        
        image_config = load_image_config()
        
        st.subheader("Configuration de l'image")
        
        # Choix du type d'image (en dehors du formulaire pour plus de réactivité)
        image_type = st.radio(
            "Type d'image",
            ["none", "local", "url"],
            format_func=lambda x: {
                "none": "Aucune image",
                "local": "📁 Image depuis mon PC",
                "url": "🌐 Image depuis une URL"
            }[x],
            index=["none", "local", "url"].index(image_config.get("image_type", "none"))
        )
        
        # Formulaire avec les champs appropriés selon le type sélectionné
        with st.form("image_form"):
            image_url = ""
            uploaded_file = None
            
            if image_type == "url":
                st.info("💡 Entrez l'URL complète d'une image hébergée sur internet")
                # URL de l'image
                image_url = st.text_input(
                    "URL de l'image",
                    value=image_config.get("image_url", "") if image_config.get("image_type") == "url" else "",
                    placeholder="https://exemple.com/image.jpg"
                )
            elif image_type == "local":
                st.info("📤 Sélectionnez une image depuis votre ordinateur")
                # Upload d'image locale
                uploaded_file = st.file_uploader(
                    "Choisir une image depuis votre PC",
                    type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
                    help="Formats supportés : PNG, JPG, JPEG, GIF, BMP. L'image sera automatiquement redimensionnée si nécessaire.",
                    key="image_uploader"
                )
                
                # Afficher un aperçu de l'image uploadée
                if uploaded_file is not None:
                    st.success(f"✅ Image sélectionnée : {uploaded_file.name}")
                    try:
                        # Prévisualisation de l'image uploadée
                        image_preview = Image.open(uploaded_file)
                        st.image(image_preview, caption="Aperçu de l'image à uploader", width=300)
                        # Remettre le pointeur au début du fichier
                        uploaded_file.seek(0)
                    except Exception as e:
                        st.error("Erreur lors de la prévisualisation de l'image")
            elif image_type == "none":
                st.info("❌ Aucune image ne sera affichée sur la page d'accueil")
            
            # Légende de l'image (seulement si ce n'est pas "none")
            image_caption = ""
            if image_type != "none":
                image_caption = st.text_input(
                    "Légende de l'image (optionnel)",
                    value=image_config.get("image_caption", ""),
                    placeholder="Description de l'image"
                )
            
            submitted = st.form_submit_button("💾 Sauvegarder la configuration", type="primary", use_container_width=True)
            
            if submitted:
                new_config = {
                    "image_type": image_type,
                    "image_url": "",
                    "image_path": "",
                    "image_caption": image_caption.strip()
                }
                
                if image_type == "url" and image_url.strip():
                    new_config["image_url"] = image_url.strip()
                    st.success("✅ Configuration URL sauvegardée !")
                elif image_type == "local":
                    if uploaded_file is not None:
                        # Sauvegarder l'image uploadée
                        saved_path = save_uploaded_image(uploaded_file)
                        if saved_path:
                            new_config["image_path"] = saved_path
                            # Supprimer l'ancienne image si elle existe
                            old_config = load_image_config()
                            if (old_config.get("image_type") == "local" and 
                                old_config.get("image_path") and 
                                os.path.exists(old_config["image_path"]) and
                                old_config["image_path"] != saved_path):
                                try:
                                    os.remove(old_config["image_path"])
                                except:
                                    pass
                            st.success("✅ Image uploadée et sauvegardée !")
                        else:
                            st.error("❌ Erreur lors de la sauvegarde de l'image")
                            st.stop()
                    elif image_config.get("image_type") == "local" and image_config.get("image_path"):
                        # Garder l'image existante si aucune nouvelle image n'est uploadée
                        new_config["image_path"] = image_config.get("image_path", "")
                        st.success("✅ Configuration sauvegardée (image existante conservée)")
                    else:
                        st.warning("⚠️ Aucune image sélectionnée. Sélectionnez une image ou choisissez un autre type.")
                        st.stop()
                elif image_type == "none":
                    st.success("✅ Configuration sauvegardée (aucune image)")
                
                save_image_config(new_config)
                st.rerun()
        
        # Prévisualisation
        st.subheader("Prévisualisation actuelle")
        if not display_image_from_config():
            pass  # Message déjà affiché dans display_image_from_config()
        
        # Gestion des images uploadées
        st.subheader("Gestion des fichiers")
        if os.path.exists(IMAGES_FOLDER):
            image_files = [f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            if image_files:
                st.write(f"**{len(image_files)} image(s) stockée(s) localement**")
                
                # Calculer la taille totale
                total_size = 0
                for file in image_files:
                    filepath = os.path.join(IMAGES_FOLDER, file)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
                
                size_mb = total_size / (1024 * 1024)
                st.write(f"Espace utilisé : {size_mb:.2f} MB")
                
                # Option pour nettoyer les anciennes images
                if st.button("Nettoyer les images non utilisées", help="Supprime toutes les images sauf celle actuellement configurée"):
                    current_image = image_config.get("image_path", "")
                    deleted_count = 0
                    
                    for file in image_files:
                        filepath = os.path.join(IMAGES_FOLDER, file)
                        if filepath != current_image:
                            try:
                                os.remove(filepath)
                                deleted_count += 1
                            except:
                                pass
                    
                    if deleted_count > 0:
                        st.success(f"{deleted_count} image(s) supprimée(s)")
                        st.rerun()
                    else:
                        st.info("Aucune image à supprimer")
            else:
                st.info("Aucune image stockée localement")
    
    with tab6:
        st.header("Gestion du contenu personnalisé")
        st.info("💡 Ce contenu apparaîtra dans la colonne de gauche de la page d'accueil, à côté de l'image")
        
        content_config = load_content_config()
        
        # Prévisualisation du contenu actuel
        if content_config.get("elements"):
            st.subheader("📋 Prévisualisation du contenu actuel")
            with st.container():
                st.markdown("---")
                display_custom_content()
                st.markdown("---")
        else:
            st.info("Aucun contenu personnalisé configuré")
        
        st.subheader("➕ Ajouter un nouvel élément")
        
        with st.form("add_content_element"):
            element_type = st.selectbox(
                "Type d'élément",
                ["text", "image", "spacer"],
                format_func=lambda x: {
                    "text": "📝 Texte",
                    "image": "🖼️ Image", 
                    "spacer": "📏 Espace"
                }[x]
            )
            
            if element_type == "text":
                text_style = st.selectbox(
                    "Style de texte",
                    ["normal", "header", "subheader", "markdown"],
                    format_func=lambda x: {
                        "normal": "Texte normal",
                        "header": "Titre principal",
                        "subheader": "Sous-titre",
                        "markdown": "Markdown (formatage avancé)"
                    }[x]
                )
                
                if text_style == "markdown":
                    st.info("💡 Vous pouvez utiliser la syntaxe Markdown : **gras**, *italique*, [lien](url), etc.")
                
                text_content = st.text_area(
                    "Contenu du texte",
                    placeholder="Entrez votre texte ici...",
                    height=100
                )
                
            elif element_type == "image":
                image_source = st.radio(
                    "Source de l'image",
                    ["url", "local"],
                    format_func=lambda x: {"url": "🌐 URL", "local": "📁 Fichier local"}[x]
                )
                
                image_url = ""
                uploaded_image = None
                
                if image_source == "url":
                    image_url = st.text_input(
                        "URL de l'image",
                        placeholder="https://exemple.com/image.jpg"
                    )
                else:
                    uploaded_image = st.file_uploader(
                        "Choisir une image",
                        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
                        key="content_image_uploader"
                    )
                
                image_caption = st.text_input("Légende (optionnel)")
                image_width = st.number_input("Largeur de l'image (pixels, 0 = automatique)", min_value=0, max_value=800, value=0)
                
            elif element_type == "spacer":
                spacer_height = st.number_input("Hauteur de l'espace (pixels)", min_value=10, max_value=200, value=30)
            
            add_element = st.form_submit_button("➕ Ajouter l'élément", type="primary")
            
            if add_element:
                new_element = {"type": element_type}
                
                if element_type == "text":
                    if not text_content.strip():
                        st.error("Le contenu du texte ne peut pas être vide")
                    else:
                        new_element.update({
                            "style": text_style,
                            "content": text_content.strip()
                        })
                        
                elif element_type == "image":
                    if image_source == "url":
                        if not image_url.strip():
                            st.error("L'URL de l'image ne peut pas être vide")
                        else:
                            new_element.update({
                                "image_type": "url",
                                "image_url": image_url.strip(),
                                "caption": image_caption.strip(),
                                "width": image_width if image_width > 0 else None
                            })
                    else:  # local
                        if uploaded_image is None:
                            st.error("Veuillez sélectionner une image")
                        else:
                            saved_path = save_uploaded_image(uploaded_image)
                            if saved_path:
                                new_element.update({
                                    "image_type": "local",
                                    "image_path": saved_path,
                                    "caption": image_caption.strip(),
                                    "width": image_width if image_width > 0 else None
                                })
                            else:
                                st.error("Erreur lors de la sauvegarde de l'image")
                                st.stop()
                                
                elif element_type == "spacer":
                    new_element.update({
                        "height": spacer_height
                    })
                
                # Ajouter l'élément à la configuration
                if "content" in new_element or "image_url" in new_element or "image_path" in new_element or "height" in new_element:
                    content_config["elements"].append(new_element)
                    save_content_config(content_config)
                    st.success("✅ Élément ajouté avec succès !")
                    st.rerun()
        
        # Gestion des éléments existants
        if content_config.get("elements"):
            st.subheader("🗂️ Gérer les éléments existants")
            
            for i, element in enumerate(content_config["elements"]):
                with st.expander(f"Élément {i+1} - {element['type'].title()}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        if element["type"] == "text":
                            st.write(f"**Style:** {element.get('style', 'normal')}")
                            content_preview = element.get('content', '')[:100]
                            if len(element.get('content', '')) > 100:
                                content_preview += "..."
                            st.write(f"**Contenu:** {content_preview}")
                        elif element["type"] == "image":
                            st.write(f"**Source:** {element.get('image_type', 'inconnue')}")
                            if element.get('caption'):
                                st.write(f"**Légende:** {element['caption']}")
                        elif element["type"] == "spacer":
                            st.write(f"**Hauteur:** {element.get('height', 0)}px")
                    
                    with col2:
                        if st.button("⬆️ Monter", key=f"up_{i}", disabled=(i == 0)):
                            # Échanger avec l'élément précédent
                            content_config["elements"][i], content_config["elements"][i-1] = \
                                content_config["elements"][i-1], content_config["elements"][i]
                            save_content_config(content_config)
                            st.rerun()
                        
                        if st.button("⬇️ Descendre", key=f"down_{i}", disabled=(i == len(content_config["elements"])-1)):
                            # Échanger avec l'élément suivant
                            content_config["elements"][i], content_config["elements"][i+1] = \
                                content_config["elements"][i+1], content_config["elements"][i]
                            save_content_config(content_config)
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Supprimer", key=f"delete_{i}", type="secondary"):
                            # Supprimer l'image locale si c'est une image locale
                            if (element["type"] == "image" and 
                                element.get("image_type") == "local" and 
                                element.get("image_path") and 
                                os.path.exists(element["image_path"])):
                                try:
                                    os.remove(element["image_path"])
                                except:
                                    pass
                            
                            # Supprimer l'élément
                            content_config["elements"].pop(i)
                            save_content_config(content_config)
                            st.success("Élément supprimé !")
                            st.rerun()
            
            # Bouton pour tout effacer
            st.markdown("---")
            if st.button("🗑️ Effacer tout le contenu personnalisé", type="secondary"):
                # Supprimer toutes les images locales
                for element in content_config.get("elements", []):
                    if (element["type"] == "image" and 
                        element.get("image_type") == "local" and 
                        element.get("image_path") and 
                        os.path.exists(element["image_path"])):
                        try:
                            os.remove(element["image_path"])
                        except:
                            pass
                
                save_content_config({"elements": []})
                st.success("Tout le contenu personnalisé a été effacé !")
                st.rerun()

def main():
    """Fonction principale"""
    init_session_state()
    
    # Sidebar pour la navigation
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("Accueil", use_container_width=True):
            st.session_state.page = 'accueil'
            st.rerun()
        
        if st.button("Inscription", use_container_width=True):
            st.session_state.page = 'inscription'
            st.rerun()
        
        if st.button("Modérateurs", use_container_width=True):
            st.session_state.page = 'moderator'
            st.rerun()
        
        if st.session_state.logged_in:
            st.success("Connecté en tant que modérateur")
            if st.button("Se déconnecter", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.page = 'accueil'
                st.rerun()
        
        # Informations visibles seulement pour les modérateurs
        if st.session_state.logged_in:
            st.markdown("---")
            st.markdown("### Informations")
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
    if st.session_state.page == 'accueil':
        home_page()
    elif st.session_state.page == 'inscription':
        registration_page()
    elif st.session_state.page == 'moderator':
        if not st.session_state.logged_in:
            moderator_login()
        else:
            moderator_dashboard()

if __name__ == "__main__":
    main()
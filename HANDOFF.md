# Reprise du projet - Le Réflexe Dos

Date de transmission : 5 octobre 2026  
Projet : site éditorial et boutique numérique autour de la lombalgie commune  
Nom de travail : Le Réflexe Dos

## Objectif

Construire une marque francophone utile, prudente et accessible autour du mal de dos : site public, contenus SEO, guides numériques, fiches pratiques, programme de 28 jours, collecte e-mail et vente de fichiers numériques.

Le positionnement n'est pas de promettre une guérison. La promesse éditoriale est : comprendre, bouger progressivement et savoir quand demander de l'aide.

## Ce qui est déjà disponible

### Site statique

- `index.html` : accueil et tunnel principal.
- `boutique.html` : catalogue, prix et démonstration de panier.
- `magazine.html` : architecture de contenus SEO.
- `a-propos.html` : méthode, sources et validation santé.
- `mentions-legales.html` : trame à compléter par le responsable légal.
- `assets/styles.css` et `assets/app.js` : identité visuelle, responsive et interactions locales.
- `assets/images/` : photos et illustrations originales générées pour le projet.

Le site fonctionne localement sans installation : ouvrir `index.html`. Le panier et les formulaires sont des démonstrations et n'envoient aucune donnée.

### Documents de cadrage

- `docs/analyse-reference-runweek.md` : analyse du modèle de mise en page de référence.
- `docs/analyse-agenda-runweek-2027.md` : principes de structure, rythme et usages.
- `docs/direction-artistique-visuels.md` : direction artistique et garde-fous d'images.
- `docs/strategie-commerciale.md` : produits, prix, acquisition, prospection et communication.
- `docs/architecture-dynamique.md` : architecture cible avec PostgreSQL, Stripe, Brevo, OpenRouter et Apify.
- `docs/schema-postgresql.sql` : schéma de base de données de départ.

### Produits PDF finaux en cours de validation

- `output/pdf/SOS-Lumbago-guide-illustre-edition-finale-48-pages.pdf` : guide complet, 48 pages.
- `output/pdf/Fiches-pratiques-Le-Reflexe-Dos-edition-finale-32-pages.pdf` : collection complète, 32 pages et 24 fiches extractibles.

Les deux PDF ont été contrôlés sur la pagination, le rendu visuel et la taille minimale réelle des polices : 12 pt. La validation médicale n'est pas encore acquise et doit être réalisée avant commercialisation.

## Génération des PDF

Le générateur principal est `production/build_final_products.py`.

Dépendances Python attendues : `reportlab`, `Pillow`, `pypdf`. Commande de génération :

```powershell
python production/build_final_products.py
```

Le script utilise les images dans `assets/images/` et écrit dans `output/pdf/`. Toute nouvelle édition doit conserver une police minimale de 12 pt et être rendue en PNG pour un contrôle visuel.

## Priorités de reprise

1. Faire relire le guide et les fiches par un médecin ou un kinésithérapeute, avec nom, qualité, date et périmètre de validation.
2. Vérifier les mentions légales, CGV, droit de rétractation du contenu numérique, politique de confidentialité et disponibilité du nom de marque.
3. Produire le cahier d'exercices `Dos Solide - 28 jours` et l'ebook pédagogique de 64 à 80 pages dans la même identité visuelle.
4. Remplacer les démonstrations locales par un site applicatif : PostgreSQL/Supabase, Stripe Checkout, stockage privé avec liens signés, Brevo double opt-in et espace client.
5. Mettre en place le workflow éditorial : brouillon -> vérification des sources -> relecture médicale -> publication.

## Règles à ne pas perdre

- Ne jamais présenter un contenu généré par IA comme une validation médicale.
- Ne pas diagnostiquer, prescrire une posologie ou personnaliser un programme à partir de données de santé.
- Conserver des sources datées pour chaque affirmation médicale.
- Ne pas envoyer de données de santé ou de données identifiantes à OpenRouter.
- Utiliser Apify uniquement pour une veille publique conforme aux conditions des sites.
- Ne jamais publier un contenu santé sans relecture humaine approuvée et non expirée.
- Garder un ton accessible, positif, non culpabilisant et orienté vers une prochaine action réaliste.

## Convention Git proposée

- `main` : versions publiables et validées.
- `feature/` : évolution du site ou d'un document.
- `content/` : manuscrits, sources et déclinaisons éditoriales.
- `review/medical-YYYY-MM` : branche de préparation à la validation santé.

Avant toute publication, vérifier le rendu mobile du site, la pagination des PDF, les liens des sources et le statut de validation médicale.

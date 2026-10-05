# Le Réflexe Dos — kit de lancement

Prototype éditorial et commercial d’un site français consacré à la lombalgie commune : contenus gratuits, guides numériques, programme progressif, affiliation et offre B2B.

## Ouvrir le site

Ouvrir `index.html` dans un navigateur. Le site fonctionne sans installation ni serveur. Le panier, les formulaires et le paiement sont des démonstrations locales : aucune donnée n’est envoyée et aucun paiement n’est déclenché.

## Livrables

- `index.html` : page d’accueil et tunnel principal.
- `boutique.html` : catalogue, contenu des offres et prix.
- `magazine.html` : architecture éditoriale SEO.
- `a-propos.html` : méthode, sources et circuit de validation santé.
- `mentions-legales.html` : trame de conformité à compléter.
- `assets/styles.css` : identité visuelle et responsive.
- `assets/app.js` : panier de démonstration, formulaires et interactions.
- `assets/images/` : série photographique générée, en PNG source et WebP optimisé.
- `docs/analyse-reference-runweek.md` : analyse du site Claude fourni.
- `docs/analyse-agenda-runweek-2027.md` : analyse de l’agenda et transposition aux futurs supports éditoriaux.
- `docs/direction-artistique-visuels.md` : usages, garde-fous et prompts des images.
- `docs/strategie-commerciale.md` : offres, supports, acquisition, prospection et calendrier.
- `docs/architecture-dynamique.md` : passage du prototype au produit dynamique.
- `docs/schema-postgresql.sql` : schéma PostgreSQL recommandé.

## Décisions de positionnement

Nom de travail : **Le Réflexe Dos**. Promesse : « comprendre, bouger progressivement et savoir quand demander de l’aide ». Le site ne vend pas une guérison et ne pose aucun diagnostic.

Le lancement reste soumis à deux validations : disponibilité juridique et commerciale du nom/domaine, puis relecture de chaque contenu santé par un professionnel qualifié.

## État de la production au 5 octobre 2026

Le projet contient maintenant deux produits PDF finalisés en pagination commerciale :

- `output/pdf/SOS-Lumbago-guide-illustre-edition-finale-48-pages.pdf` : guide illustré de 48 pages.
- `output/pdf/Fiches-pratiques-Le-Reflexe-Dos-edition-finale-32-pages.pdf` : collection de 32 pages avec 24 fiches autonomes et extractibles.

Les fichiers ont été générés avec une taille de police minimale de 12 pt. Ils restent des supports éditoriaux de travail : le contenu santé, les illustrations de mouvement, les mentions légales et l'identité commerciale doivent être relus et validés avant la vente.

## Reprendre le projet avec un autre LLM

Commencer par lire `HANDOFF.md`, puis `WORKLOG.md`, `docs/architecture-dynamique.md`, `docs/schema-postgresql.sql` et `docs/strategie-commerciale.md`.

Le générateur des deux éditions finales est `production/build_final_products.py`. Il utilise Python, ReportLab, Pillow et pypdf. Pour régénérer les PDF :

```powershell
python production/build_final_products.py
```

Le dossier `output/pdf/` contient les versions finales ainsi que les versions de travail précédentes. Ne pas supprimer les anciennes versions avant d'avoir confirmé la validation éditoriale et médicale.

## Archive de transmission

Une archive ZIP de transmission est créée à côté du dossier du projet. Elle contient les pages HTML/CSS/JS, les visuels, les analyses, les sources PDF, les manuscrits, les générateurs et les deux supports finaux. Les dossiers temporaires de rendu et caches locaux sont exclus.

## Déploiement statique

Le prototype peut être déposé sur Cloudflare Pages, Netlify ou Vercel comme site statique. Pour la version commerciale, suivre `docs/architecture-dynamique.md` afin de connecter les paiements, téléchargements privés, e-mails et PostgreSQL.


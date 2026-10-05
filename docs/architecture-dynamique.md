# Passage du prototype au site dynamique

## 1. Recommandation en une phrase

Conserver le front éditorial rapide, puis ajouter **Next.js ou Astro avec fonctions serveur, Supabase/PostgreSQL, Stripe Checkout, stockage privé, Brevo et un pipeline de contenu assisté par OpenRouter, avec Apify limité à la veille publique**.

## 2. Architecture cible

```text
Navigateur
   │
   ├── pages publiques, SEO, boutique
   ├── espace client protégé
   └── formulaires sans données de santé
   │
CDN / application (Cloudflare Pages ou Vercel)
   │
   ├── API applicative
   ├── Stripe Checkout + webhooks
   ├── Brevo double opt-in
   ├── stockage privé + liens signés
   └── file de tâches éditoriales
           │
PostgreSQL / Supabase
   ├── contenus, versions, sources, relectures
   ├── produits, commandes, droits d’accès
   ├── consentements et campagnes
   └── journaux d’automatisation
           │
   ├── OpenRouter : brouillons, variantes, extraction d’affirmations
   └── Apify : collecte planifiée de sources publiques et tendances
```

## 3. Stack recommandée pour le MVP

### Front et application

**Option recommandée : Next.js sur Vercel**

- Bon compromis pour pages SEO, API, espace client et intégration Stripe.
- Rendu statique pour les articles, rendu serveur pour les droits d’accès.
- Déploiements de prévisualisation utiles pour la relecture médicale.

**Alternative légère : Astro sur Cloudflare Pages**

- Excellent pour un site éditorial majoritairement statique.
- Ajouter Cloudflare Workers pour Stripe, les formulaires et les liens signés.
- Plus sobre, mais l’espace client demandera davantage d’assemblage.

**Alternative CMS : WordPress + WooCommerce**

- Lancement rapide et back-office familier.
- Utiliser un thème léger, un plugin de téléchargement protégé et un cache CDN.
- Inconvénients : surface de sécurité, dépendance aux extensions et maintenance plus lourde.

### PostgreSQL

**Supabase est recommandé au départ** : vrai PostgreSQL, authentification, stockage, API, fonctions et règles de sécurité par ligne réunis. Les tables exposées au client doivent utiliser Row Level Security ; sans politique, l’accès doit être refusé.

Alternatives :

- **Neon + Clerk/Auth.js + Cloudflare R2** : très bon pour le serverless, branches de base de données, autoscaling et scale-to-zero. Plus modulaire, donc plus de configuration.
- **PostgreSQL managé sur Scaleway/OVH/AWS RDS** : contrôle et localisation à choisir, mais davantage d’exploitation.
- **PostgreSQL auto-hébergé** : déconseillé au lancement sauf compétence d’astreinte, sauvegardes testées et supervision existante.

### Paiement et livraison

- Stripe Checkout hébergé pour éviter de manipuler les cartes.
- Le webhook `checkout.session.completed` crée la commande payée et les droits d’accès.
- Les fichiers ne sont jamais publics : bucket privé et URL signée de courte durée.
- Enregistrer chaque téléchargement pour le support et la détection d’abus, sans profilage intrusif.
- Le checkout doit recueillir séparément l’accord d’accès immédiat et la reconnaissance de perte du droit de rétractation applicable au contenu numérique.

### E-mail

- Brevo au lancement : double opt-in, automatisation simple et coût contenu.
- Customer.io devient pertinent si le parcours dépend de nombreux événements produit.
- Stocker dans PostgreSQL la preuve du consentement, la version du texte, la source et l’horodatage ; ne pas stocker seulement un booléen.

## 4. Modèle de données

Le fichier `schema-postgresql.sql` fournit une base exécutable. Les blocs fonctionnels sont :

### Identité et consentement

- `profiles` : compte client minimal.
- `consent_events` : preuve immuable du consentement ou du retrait.
- `lead_subscriptions` : état marketing et double opt-in.

### Commerce

- `products` et `product_prices` : catalogue versionné.
- `orders` et `order_items` : historique financier stable.
- `entitlements` : droit d’accéder à une version de produit.
- `download_events` : audit des livraisons numériques.

### Éditorial et sécurité santé

- `content_items` : article, page, e-mail, guide ou script vidéo.
- `content_versions` : texte versionné et statut de workflow.
- `sources` et `content_sources` : traçabilité des références.
- `medical_reviews` : relecteur, décision, portée et date d’expiration.
- `claims` : affirmations de santé extraites et vérifiées une par une.
- `correction_reports` : signalement et résolution publique.

### Acquisition

- `campaigns` et `campaign_assets` : campagnes et créations.
- `affiliate_links` et `affiliate_clicks` : redirections centralisées et déclaration.
- `seo_keywords` : intention, cluster, page cible et suivi.
- `automation_runs` : coût, statut et sortie de chaque tâche Apify/OpenRouter.

## 5. États de publication obligatoires

```text
idea → brief → draft → source_check → medical_review → ready → published
                    ↘ rejected                    ↘ archived
```

Règles :

- Seul le rôle `publisher` peut passer un contenu à `published`.
- Un contenu santé exige une revue `approved` non expirée.
- Toute modification d’une affirmation médicale crée une nouvelle version et annule l’approbation précédente.
- Une publication planifiée échoue si une source obligatoire manque ou si la revue a expiré.
- Le front n’affiche que la version publiée, jamais le brouillon le plus récent.

## 6. API minimale

| Méthode | Route | Usage |
|---|---|---|
| `POST` | `/api/leads` | Début du double opt-in |
| `GET` | `/api/confirm-subscription` | Confirmation e-mail signée |
| `POST` | `/api/checkout` | Création de session Stripe |
| `POST` | `/api/webhooks/stripe` | Paiement et droits d’accès |
| `GET` | `/api/library` | Produits accessibles au client |
| `POST` | `/api/download-link` | URL signée après contrôle du droit |
| `POST` | `/api/correction-reports` | Signaler une ambiguïté ou erreur |
| `POST` | `/api/admin/content/draft` | Créer une version de brouillon |
| `POST` | `/api/admin/content/review` | Enregistrer une relecture |
| `POST` | `/api/admin/content/publish` | Publier après contrôles bloquants |

## 7. OpenRouter : usage recommandé

OpenRouter offre un point d’accès compatible avec l’API OpenAI et permet de choisir plusieurs modèles ou des modèles de repli. Le projet doit l’utiliser comme **assistant de production**, jamais comme autorité médicale.

### Tâches autorisées

- Transformer une liste de mots-clés en briefs éditoriaux.
- Proposer trois angles et cinq titres non sensationnalistes.
- Résumer une source déjà fournie, avec passages à vérifier.
- Extraire les affirmations de santé d’un brouillon dans un JSON structuré.
- Adapter un article validé en script vidéo, carrousel ou e-mail.
- Détecter les formulations absolues : « guérit », « sans danger », « fonctionne pour tous ».

### Tâches interdites sans validation humaine

- Inventer une recommandation ou compléter une source absente.
- Donner un diagnostic, un pronostic ou une posologie.
- Personnaliser un programme à partir de données de santé.
- Publier automatiquement un contenu santé.
- Envoyer à un fournisseur IA des données identifiantes ou des réponses médicales.

### Pipeline proposé

1. Le brief définit le public, l’intention, les sources autorisées et les phrases interdites.
2. Le modèle renvoie un brouillon et une liste JSON d’affirmations.
3. Le serveur vérifie que chaque citation pointe vers une source enregistrée.
4. Un second modèle peut critiquer le brouillon, mais son avis reste indicatif.
5. Le relecteur médical décide : approuvé, corrections demandées ou rejeté.
6. L’éditeur publie explicitement la version approuvée.

### Routage et coûts

- Modèle rapide et économique pour les titres, classifications et transformations.
- Modèle plus capable pour les longs brouillons et la critique.
- Liste de repli uniquement pour la disponibilité ; enregistrer le modèle réellement utilisé.
- Pour chaque appel : modèle, fournisseur, tokens, coût, latence, version du prompt et hachage du contenu.
- Plafond quotidien et coupe-circuit si le coût ou le taux d’erreur dépasse le seuil.

### Confidentialité

Les entrées sont transmises au fournisseur de modèle choisi par OpenRouter. Les pratiques de conservation et d’entraînement varient selon les fournisseurs. Sélectionner des fournisseurs sans entraînement sur les données, exclure toute donnée de santé ou donnée personnelle et conclure les accords nécessaires avant un usage réel.

## 8. Apify : veille et collecte

Les Actors Apify sont des programmes cloud qui acceptent une entrée JSON, exécutent une collecte ou un traitement et produisent des données structurées. Ils peuvent être exécutés par API ou planification.

### Usages pertinents

- Surveiller les pages officielles HAS, OMS, Ameli et INRS pour détecter une mise à jour.
- Relever les titres et dates de concurrents publics pour cartographier les sujets couverts.
- Collecter les tendances publiques et commentaires autorisés pour identifier des questions, sans constituer de profils.
- Vérifier les prix publics et politiques de retour des marchands affiliés.
- Alimenter une file `source_candidates`, jamais directement la publication.

### Flux recommandé

```text
Schedule Apify hebdomadaire
  → Actor limité aux domaines autorisés
  → Dataset JSON
  → Webhook signé vers l’application
  → déduplication par URL + hash
  → enregistrement source_candidates
  → tri OpenRouter facultatif
  → validation éditoriale humaine
```

### Garde-fous

- Respecter les conditions d’utilisation, robots.txt, droits d’auteur et limites de fréquence.
- Ne pas contourner de connexion, CAPTCHA, paywall ou mesure anti-bot.
- Ne pas aspirer d’e-mails personnels pour la prospection B2C.
- Conserver l’URL, la date d’accès, le hash et seulement l’extrait nécessaire.
- Supprimer ou actualiser les données devenues fausses.
- Apify peut stocker ses résultats en datasets exportables ; PostgreSQL reste la source durable de vérité.

### Coût de départ

Le plan gratuit permet un petit budget d’usage. Le plan Starter est affiché à 19 USD/mois plus usage ; le passage au payant n’est utile que lorsque la veille automatisée économise réellement du temps. Commencer avec deux tâches hebdomadaires et un plafond strict.

## 9. Alternatives d’automatisation

| Besoin | Solution recommandée | Alternatives |
|---|---|---|
| Orchestration simple | Cron Vercel/Cloudflare + fonctions | GitHub Actions, pg_cron |
| Workflows visuels | n8n auto-hébergé | Make, Zapier |
| Scraping public | Apify/Crawlee | Firecrawl, scripts Playwright maîtrisés |
| Rédaction assistée | OpenRouter | API directe d’un fournisseur, modèles locaux |
| Recherche sémantique | PostgreSQL + pgvector | Typesense, Meilisearch, OpenSearch |
| CMS | Tables PostgreSQL + back-office interne | Sanity, Strapi, Directus, WordPress headless |
| Analytics sobre | Plausible ou Matomo | GA4 avec consentement adapté |

## 10. Sécurité et conformité par conception

- Aucun champ de symptômes libre dans le MVP.
- Secrets uniquement côté serveur et rotation planifiée.
- Vérification de signature des webhooks Stripe, Brevo et Apify.
- Liens de téléchargement à usage limité et courte expiration.
- Journal d’administration immuable : qui a relu, modifié, publié ou remboursé.
- Sauvegarde quotidienne PostgreSQL et test de restauration trimestriel.
- RLS sur toutes les tables accessibles depuis le navigateur.
- Politique de conservation : prospects non confirmés 30 jours, consentements selon preuve légale, commandes selon obligations comptables, logs techniques courts.
- Export et suppression des données utilisateur automatisables.
- Bannière cookies seulement si nécessaire ; préférer une mesure sans traceur non essentiel au lancement.

## 11. Plan d’implémentation

### Lot 1 — 3 à 5 jours

- Transformer le prototype en composants.
- Configurer domaine, HTTPS, pages légales et analytics sobre.
- Brancher Brevo double opt-in et stocker la preuve de consentement.

### Lot 2 — 4 à 7 jours

- Déployer PostgreSQL/Supabase et migrations.
- Configurer produits, prix, Stripe Checkout et webhooks.
- Créer l’espace client et les téléchargements signés.

### Lot 3 — 4 à 6 jours

- Créer le back-office contenu, sources, versions et relectures.
- Implémenter le blocage de publication sans approbation santé.
- Ajouter le formulaire de correction.

### Lot 4 — 3 à 5 jours

- Ajouter OpenRouter pour briefs, extraction d’affirmations et déclinaisons.
- Ajouter Apify pour la veille officielle hebdomadaire.
- Mettre les plafonds de coût, logs et alertes.

### Lot 5 — avant ouverture commerciale

- Test complet du paiement, remboursement, lien expiré et achat en double.
- Test mobile, accessibilité clavier, lecteurs d’écran et contraste.
- Audit juridique, RGPD, CGV et médiation.
- Validation médicale de toutes les pages et de chaque exercice.
- Sauvegarde et restauration testées.

## 12. Budget technique mensuel de départ

| Poste | Ordre de grandeur |
|---|---:|
| Hébergement front | 0–20 € |
| Supabase/PostgreSQL | 0–25 € |
| E-mail | 0–19 € |
| Stockage et CDN | 0–10 € |
| OpenRouter | plafond 20–50 € |
| Apify | 0 €, puis 19 USD + usage |
| Analytics | 0–19 € |
| Total MVP | environ 20–120 €/mois hors frais Stripe |

## 13. Sources techniques

- [Supabase — Database overview](https://supabase.com/docs/guides/database/overview) : PostgreSQL complet, sauvegardes, RLS, extensions et fonctions.
- [Supabase — Connexions PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres) : connexion directe, poolers et contraintes serverless.
- [Neon — Database branching workflow](https://neon.com/docs/get-started-with-neon/workflow-primer) : branches isolées et scale-to-zero.
- [OpenRouter — Quickstart](https://openrouter.ai/docs/quickstart) : endpoint unifié et compatibilité API.
- [OpenRouter — Model fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks) : modèles de repli et facturation du modèle réellement utilisé.
- [OpenRouter — Privacy policy](https://openrouter.ai/privacy/) : transmission des entrées aux fournisseurs et pratiques variables.
- [Apify — Actors](https://docs.apify.com/actors) : programmes cloud JSON, API, planification et sorties structurées.
- [Apify — Datasets](https://docs.apify.com/storage/dataset) : stockage, export et durée de rétention.
- [Apify — Pricing](https://apify.com/pricing) : prix affichés au moment du cadrage.

Les prix et fonctionnalités de services évoluent. Les vérifier à nouveau au moment de l’implémentation.


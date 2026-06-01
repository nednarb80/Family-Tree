# Publishing the tree online (one-time setup)

This puts the family tree on a **free public website** with the interactive
relationship graph, using [Quartz](https://quartz.jzhao.xyz) + GitHub Pages. You do
this once; after that, every change you push updates the site automatically.

Verified against Quartz v4 (current as of 2026). Official guide:
<https://quartz.jzhao.xyz/hosting>.

## What you need

- A free [GitHub](https://github.com) account
- [Node.js](https://nodejs.org) 22+ and [git](https://git-scm.com) installed
- This vault

## Step 1 — Put the vault on GitHub

Create a new repository on GitHub (e.g. `collins-family-tree`). Then, in this
folder:

```bash
git init
git add .
git commit -m "Family tree archive — initial import"
git branch -M main
git remote add origin https://github.com/<you>/collins-family-tree.git
git push -u origin main
```

## Step 2 — Set up Quartz

Quartz needs to live alongside your content. The cleanest pattern: clone Quartz,
then point it at this vault's markdown as its `content`.

```bash
git clone https://github.com/jackyzha0/quartz.git
cd quartz
npm install
npx quartz create      # choose "Empty Quartz", then the default
```

Copy the two config files from this vault's `quartz/` folder over the defaults:

```bash
cp ../path-to-this-vault/quartz/quartz.config.ts .
cp ../path-to-this-vault/quartz/quartz.layout.ts .
```

(They're pre-filled with the family-tree title, graph view, backlinks, and search.)

Preview locally — this opens the site at <http://localhost:8080> and live-reloads:

```bash
npx quartz build --serve
```

Point Quartz's `content` at this vault's people/families/places/sources, or simply
copy the markdown into Quartz's `content/` folder. For an always-in-sync setup, make
`content` a symlink to the vault (Quartz docs cover this under "i18n / multiple
content folders").

## Step 3 — Turn on GitHub Pages

1. Add the deploy workflow: this vault already ships
   `.github/workflows/deploy.yml`. Make sure it's in the repo you push Quartz from.
2. On GitHub: **Settings → Pages → Source → GitHub Actions**.
3. Push. The Action builds the site and publishes it. Your URL will be
   `https://<you>.github.io/collins-family-tree/`.

Set that URL as `baseUrl` in `quartz.config.ts` so links and the graph resolve
correctly.

## Step 4 — Updating the site later

Any time you change the tree:

```bash
git add . && git commit -m "what changed" && git push
```

The Action rebuilds and republishes within a couple of minutes. That's the whole
loop.

## Controlling what's public

By default everything publishes. Two common adjustments:

- **Hide living people.** Add `ExplicitPublish` to the config's filters so only
  pages with `publish: true` in their frontmatter appear — or the inverse, exclude
  anything tagged `living?`. The confidence work already tags living people, so you
  can filter on that.
- **Keep the inbox private.** Add `_inbox` to the ignore list in
  `quartz.config.ts` (`ignorePatterns`) so unprocessed documents don't go public.

Both are one-line edits in `quartz.config.ts`; comments in that file mark where.

import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Quartz configuration for the Collins Family Tree.
 *
 * This file controls the published site's title, theme, and which content goes
 * public. Drop it into your Quartz clone (replacing the default quartz.config.ts).
 * Full reference: https://quartz.jzhao.xyz/configuration
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "The Collins Family Tree",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,        // hover-preview of linked people — great for a tree
    analytics: null,             // keep it private; no tracking
    locale: "en-US",

    // ⚠️ After you enable GitHub Pages, set this to your real URL, e.g.
    //    "branden.github.io/collins-family-tree"
    baseUrl: "example.github.io/collins-family-tree",

    // Don't publish the working folders. _inbox holds unprocessed docs; templates
    // and scripts aren't content. (Leading patterns are matched anywhere in path.)
    ignorePatterns: ["_inbox", "templates", "scripts", ".github", "docs", "private"],

    defaultDateType: "created",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Schibsted Grotesk",
        body: "Source Sans Pro",
        code: "IBM Plex Mono",
      },
      colors: {
        // warm, archival palette
        lightMode: {
          light: "#faf8f0", lightgray: "#e6e1d4", gray: "#b8b0a0",
          darkgray: "#4a4438", dark: "#2b2820", secondary: "#7a5c3e",
          tertiary: "#a8763e", highlight: "rgba(168, 118, 62, 0.12)",
          textHighlight: "#e8d4a880",
        },
        darkMode: {
          light: "#1e1c17", lightgray: "#393530", gray: "#5e574b",
          darkgray: "#d4cdbd", dark: "#ebe5d6", secondary: "#c79a6a",
          tertiary: "#a8763e", highlight: "rgba(168, 118, 62, 0.15)",
          textHighlight: "#b3893d80",
        },
      },
    },
  },

  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({ priority: ["frontmatter", "filesystem"] }),
      Plugin.SyntaxHighlighting({ theme: { light: "github-light", dark: "github-dark" }, keepBackground: false }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),  // makes [[wikilinks]] resolve
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [
      Plugin.RemoveDrafts(),
      // To publish ONLY pages you opt in (add `publish: true` to frontmatter),
      // swap the line above for: Plugin.ExplicitPublish(),
    ],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({ enableSiteMap: true, enableRSS: true }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config

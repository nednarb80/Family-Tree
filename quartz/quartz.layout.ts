import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

/**
 * Layout for the Collins Family Tree.
 *
 * The key piece for a family tree is the Graph component (the interactive web of
 * who connects to whom) plus Backlinks (everyone who links to this person).
 * Drop this into your Quartz clone, replacing the default quartz.layout.ts.
 */

export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer({
    links: {
      "How to contribute": "https://github.com/example/collins-family-tree/blob/main/CONTRIBUTING.md",
      GitHub: "https://github.com/example/collins-family-tree",
    },
  }),
}

export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        { Component: Component.Search(), grow: true },
        { Component: Component.Darkmode() },
      ],
    }),
    Component.Explorer(),   // file/folder browser: people, sources, places
  ],
  right: [
    Component.Graph({
      // a generous local graph so you can see a person's whole cluster of kin
      localGraph: { depth: 2, scale: 1.1, showTags: false },
      globalGraph: { depth: -1, scale: 0.9, showTags: false },
    }),
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),  // "who points here" = everyone connected to this person
  ],
}

export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        { Component: Component.Search(), grow: true },
        { Component: Component.Darkmode() },
      ],
    }),
    Component.Explorer(),
  ],
  right: [],
}

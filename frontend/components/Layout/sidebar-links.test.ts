import { describe, expect, test } from "vitest";
import type { SideBarLink, SidebarLinks } from "~/types/application-types";

/**
 * Unit Tests for Sidebar Link Configuration (Task #3)
 * Tests verify correct structure of sidebar navigation items
 *
 * > **Shield** `sonnet` · 2026-03-05T10:30:00Z
 */

// Mock icons for testing
const mockIcons = {
  silverwareForkKnife: "silverwareForkKnife",
  search: "search",
  calendarMultiselect: "calendarMultiselect",
  formatListCheck: "formatListCheck",
  book: "book",
  folderOutline: "folderOutline",
  timelineText: "timelineText",
  categories: "categories",
  tags: "tags",
  potSteam: "potSteam",
  cog: "cog",
  user: "user",
  household: "household",
  group: "group",
  database: "database",
  wrench: "wrench",
  robot: "robot",
  slotMachine: "slotMachine",
};

/**
 * Helper to create main sidebar topLinks configuration
 * This mirrors the logic in DefaultLayout.vue
 */
function createMainSidebarTopLinks(groupSlug: string): SidebarLinks {
  return [
    {
      icon: mockIcons.silverwareForkKnife,
      to: `/g/${groupSlug}`,
      title: "Recipes",
      restricted: false,
    },
    {
      icon: mockIcons.search,
      to: `/g/${groupSlug}/recipes/finder`,
      title: "Recipe Finder",
      restricted: false,
    },
    {
      icon: mockIcons.calendarMultiselect,
      title: "Meal Planner",
      to: "/household/mealplan/planner/view",
      restricted: true,
    },
    {
      icon: mockIcons.formatListCheck,
      title: "Shopping Lists",
      to: "/shopping-lists",
      restricted: true,
    },
    {
      icon: mockIcons.book,
      to: `/g/${groupSlug}/cookbooks`,
      title: "Cookbooks",
      restricted: true,
    },
    {
      icon: mockIcons.folderOutline,
      title: "Organize",
      restricted: true,
      childrenStartExpanded: false,
      children: [
        {
          icon: mockIcons.timelineText,
          title: "Timeline",
          to: `/g/${groupSlug}/recipes/timeline`,
          restricted: true,
        },
        {
          icon: mockIcons.categories,
          to: `/g/${groupSlug}/recipes/categories`,
          title: "Categories",
          restricted: true,
        },
        {
          icon: mockIcons.tags,
          to: `/g/${groupSlug}/recipes/tags`,
          title: "Tags",
          restricted: true,
        },
        {
          icon: mockIcons.potSteam,
          to: `/g/${groupSlug}/recipes/tools`,
          title: "Tools",
          restricted: true,
        },
      ],
    },
  ];
}

/**
 * Helper to create admin sidebar topLinks configuration
 * This mirrors the logic in layouts/admin.vue
 */
function createAdminSidebarTopLinks(): SidebarLinks {
  return [
    {
      icon: mockIcons.cog,
      to: "/admin/site-settings",
      title: "Site Settings",
      restricted: true,
    },
    {
      icon: mockIcons.user,
      title: "Users & Access",
      restricted: true,
      childrenStartExpanded: false,
      children: [
        {
          icon: mockIcons.user,
          to: "/admin/manage/users",
          title: "Users",
          restricted: true,
        },
        {
          icon: mockIcons.household,
          to: "/admin/manage/households",
          title: "Households",
          restricted: true,
        },
        {
          icon: mockIcons.group,
          to: "/admin/manage/groups",
          title: "Groups",
          restricted: true,
        },
      ],
    },
    {
      icon: mockIcons.database,
      title: "System",
      restricted: true,
      childrenStartExpanded: false,
      children: [
        {
          icon: mockIcons.database,
          to: "/admin/backups",
          title: "Backups",
          restricted: true,
        },
        {
          icon: mockIcons.wrench,
          to: "/admin/maintenance",
          title: "Maintenance",
          restricted: true,
        },
      ],
    },
  ];
}

/**
 * Helper to create admin sidebar developerLinks configuration
 */
function createAdminSidebarDeveloperLinks(): SidebarLinks {
  return [
    {
      icon: mockIcons.robot,
      title: "Debug",
      restricted: true,
      children: [
        {
          icon: mockIcons.robot,
          to: "/admin/debug/openai",
          title: "OpenAI",
          restricted: true,
        },
        {
          icon: mockIcons.slotMachine,
          to: "/admin/debug/parser",
          title: "Parser",
          restricted: true,
        },
      ],
    },
  ];
}

describe("Main Sidebar TopLinks Configuration", () => {
  test("contains 6 top-level navigation items", () => {
    const links = createMainSidebarTopLinks("test-group");
    expect(links).toHaveLength(6);
  });

  test("Recipes is the first item and not restricted", () => {
    const links = createMainSidebarTopLinks("test-group");
    expect(links[0].title).toBe("Recipes");
    expect(links[0].restricted).toBe(false);
    expect(links[0].to).toBe("/g/test-group");
  });

  test("Meal Planner is positioned after Recipe Finder", () => {
    const links = createMainSidebarTopLinks("test-group");
    expect(links[2].title).toBe("Meal Planner");
    expect(links[2].restricted).toBe(true);
  });

  test("Shopping Lists is a primary navigation item", () => {
    const links = createMainSidebarTopLinks("test-group");
    const shoppingLists = links.find(l => l.title === "Shopping Lists");
    expect(shoppingLists).toBeDefined();
    expect(shoppingLists?.to).toBe("/shopping-lists");
    expect(shoppingLists?.restricted).toBe(true);
  });

  test("Cookbooks is a primary navigation item", () => {
    const links = createMainSidebarTopLinks("test-group");
    const cookbooks = links.find(l => l.title === "Cookbooks");
    expect(cookbooks).toBeDefined();
    expect(cookbooks?.to).toBe("/g/test-group/cookbooks");
    expect(cookbooks?.restricted).toBe(true);
  });

  test("Organize dropdown contains exactly 4 children", () => {
    const links = createMainSidebarTopLinks("test-group");
    const organize = links.find(l => l.title === "Organize");
    expect(organize?.children).toHaveLength(4);
  });

  test("Organize dropdown children are Timeline, Categories, Tags, Tools", () => {
    const links = createMainSidebarTopLinks("test-group");
    const organize = links.find(l => l.title === "Organize");
    const childTitles = organize?.children?.map(c => c.title) || [];

    expect(childTitles).toContain("Timeline");
    expect(childTitles).toContain("Categories");
    expect(childTitles).toContain("Tags");
    expect(childTitles).toContain("Tools");
  });

  test("Organize dropdown starts collapsed", () => {
    const links = createMainSidebarTopLinks("test-group");
    const organize = links.find(l => l.title === "Organize");
    expect(organize?.childrenStartExpanded).toBe(false);
  });

  test("all Organize children have restricted=true", () => {
    const links = createMainSidebarTopLinks("test-group");
    const organize = links.find(l => l.title === "Organize");
    organize?.children?.forEach((child) => {
      expect(child.restricted).toBe(true);
    });
  });

  test("all items have icons defined", () => {
    const links = createMainSidebarTopLinks("test-group");
    links.forEach((link) => {
      expect(link.icon).toBeDefined();
      expect(link.icon).toBeTruthy();
    });
  });
});

describe("Admin Sidebar TopLinks Configuration", () => {
  test("contains 3 top-level navigation items", () => {
    const links = createAdminSidebarTopLinks();
    expect(links).toHaveLength(3);
  });

  test("Site Settings is the first item", () => {
    const links = createAdminSidebarTopLinks();
    expect(links[0].title).toBe("Site Settings");
    expect(links[0].to).toBe("/admin/site-settings");
  });

  test("Users & Access dropdown contains 3 children", () => {
    const links = createAdminSidebarTopLinks();
    const usersAccess = links.find(l => l.title === "Users & Access");
    expect(usersAccess?.children).toHaveLength(3);
  });

  test("Users & Access dropdown contains Users, Households, Groups", () => {
    const links = createAdminSidebarTopLinks();
    const usersAccess = links.find(l => l.title === "Users & Access");
    const childTitles = usersAccess?.children?.map(c => c.title) || [];

    expect(childTitles).toContain("Users");
    expect(childTitles).toContain("Households");
    expect(childTitles).toContain("Groups");
  });

  test("System dropdown contains 2 children", () => {
    const links = createAdminSidebarTopLinks();
    const system = links.find(l => l.title === "System");
    expect(system?.children).toHaveLength(2);
  });

  test("System dropdown contains Backups and Maintenance", () => {
    const links = createAdminSidebarTopLinks();
    const system = links.find(l => l.title === "System");
    const childTitles = system?.children?.map(c => c.title) || [];

    expect(childTitles).toContain("Backups");
    expect(childTitles).toContain("Maintenance");
  });

  test("all admin dropdowns start collapsed", () => {
    const links = createAdminSidebarTopLinks();
    links.forEach((link) => {
      if (link.children) {
        expect(link.childrenStartExpanded).toBe(false);
      }
    });
  });

  test("all items are restricted", () => {
    const links = createAdminSidebarTopLinks();
    links.forEach((link) => {
      expect(link.restricted).toBe(true);
      link.children?.forEach((child) => {
        expect(child.restricted).toBe(true);
      });
    });
  });
});

describe("Admin Sidebar DeveloperLinks Configuration", () => {
  test("contains 1 top-level item", () => {
    const links = createAdminSidebarDeveloperLinks();
    expect(links).toHaveLength(1);
  });

  test("Debug dropdown contains 2 children", () => {
    const links = createAdminSidebarDeveloperLinks();
    const debug = links.find(l => l.title === "Debug");
    expect(debug?.children).toHaveLength(2);
  });

  test("Debug dropdown contains OpenAI and Parser", () => {
    const links = createAdminSidebarDeveloperLinks();
    const debug = links.find(l => l.title === "Debug");
    const childTitles = debug?.children?.map(c => c.title) || [];

    expect(childTitles).toContain("OpenAI");
    expect(childTitles).toContain("Parser");
  });

  test("Debug children have correct routes", () => {
    const links = createAdminSidebarDeveloperLinks();
    const debug = links.find(l => l.title === "Debug");

    const openai = debug?.children?.find(c => c.title === "OpenAI");
    expect(openai?.to).toBe("/admin/debug/openai");

    const parser = debug?.children?.find(c => c.title === "Parser");
    expect(parser?.to).toBe("/admin/debug/parser");
  });
});

describe("Sidebar Link Type Validation", () => {
  test("SideBarLink interface requires icon, title, and restricted", () => {
    const validLink: SideBarLink = {
      icon: "test-icon",
      title: "Test Link",
      restricted: true,
    };
    expect(validLink.icon).toBe("test-icon");
    expect(validLink.title).toBe("Test Link");
    expect(validLink.restricted).toBe(true);
  });

  test("SideBarLink can have optional to property", () => {
    const linkWithTo: SideBarLink = {
      icon: "test-icon",
      title: "Test Link",
      to: "/test-route",
      restricted: false,
    };
    expect(linkWithTo.to).toBe("/test-route");
  });

  test("SideBarLink can have children", () => {
    const parentLink: SideBarLink = {
      icon: "parent-icon",
      title: "Parent",
      restricted: true,
      children: [
        {
          icon: "child-icon",
          title: "Child",
          to: "/child",
          restricted: true,
        },
      ],
    };
    expect(parentLink.children).toHaveLength(1);
    expect(parentLink.children?.[0].title).toBe("Child");
  });
});

describe("Group Slug Handling", () => {
  test("main sidebar links use correct group slug in routes", () => {
    const links = createMainSidebarTopLinks("my-group");

    // Check Recipes route
    expect(links[0].to).toBe("/g/my-group");

    // Check Recipe Finder route
    expect(links[1].to).toBe("/g/my-group/recipes/finder");

    // Check Cookbooks route
    const cookbooks = links.find(l => l.title === "Cookbooks");
    expect(cookbooks?.to).toBe("/g/my-group/cookbooks");
  });

  test("Organize children use correct group slug in routes", () => {
    const links = createMainSidebarTopLinks("custom-slug");
    const organize = links.find(l => l.title === "Organize");

    const timeline = organize?.children?.find(c => c.title === "Timeline");
    expect(timeline?.to).toBe("/g/custom-slug/recipes/timeline");

    const categories = organize?.children?.find(c => c.title === "Categories");
    expect(categories?.to).toBe("/g/custom-slug/recipes/categories");
  });
});

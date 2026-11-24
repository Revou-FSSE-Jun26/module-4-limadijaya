import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Drag-and-drop and sortable libraries are forbidden (FE-14): use native HTML5 drag-and-drop.
const forbiddenDragAndDropImports = [
  { group: ["@dnd-kit/*", "dnd-kit"], message: "Use native HTML5 drag-and-drop (FE-14)." },
  { group: ["react-dnd", "react-dnd-*", "@react-dnd/*"], message: "Use native HTML5 drag-and-drop (FE-14)." },
  { group: ["react-beautiful-dnd", "@hello-pangea/dnd"], message: "Use native HTML5 drag-and-drop (FE-14)." },
  { group: ["sortablejs", "react-sortablejs", "@shopify/draggable", "dragula", "react-dragula"], message: "Use native HTML5 drag-and-drop (FE-14)." },
  { group: ["@atlaskit/pragmatic-drag-and-drop", "@atlaskit/pragmatic-drag-and-drop*"], message: "Use native HTML5 drag-and-drop (FE-14)." },
];

const eslintConfig = [
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts", "playwright-report/**", "test-results/**"],
  },
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // FE-09: no `any`.
      "@typescript-eslint/no-explicit-any": "error",
      // FE-10: Tailwind utilities only, no inline styles on DOM elements or components.
      "react/forbid-dom-props": ["error", { forbid: ["style"] }],
      "react/forbid-component-props": ["error", { forbid: ["style"] }],
      // FE-14: no drag-and-drop or sortable library.
      "no-restricted-imports": ["error", { patterns: forbiddenDragAndDropImports }],
      "no-restricted-syntax": [
        "error",
        {
          // FE-11: feature components use BaseButton, never a raw <button>.
          selector: "JSXOpeningElement[name.name='button']",
          message: "Use BaseButton instead of a raw <button> (FE-11).",
        },
        {
          // FE-21: Playwright waits on observable conditions, never a fixed delay.
          selector: "MemberExpression[property.name='waitForTimeout']",
          message: "Do not use waitForTimeout. Wait on an observable condition (FE-21).",
        },
      ],
    },
  },
  {
    // BaseButton is the only component allowed to render the <button> element (FE-11).
    // The waitForTimeout rule stays active here.
    files: ["src/components/ui/BaseButton.tsx"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "MemberExpression[property.name='waitForTimeout']",
          message: "Do not use waitForTimeout. Wait on an observable condition (FE-21).",
        },
      ],
    },
  },
];

export default eslintConfig;

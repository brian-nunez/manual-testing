### Test #8: Focus Management

- Does the page contain **interface components** that, when activated, cause the page to transition into a **new page state**[1](#footnote-focus-management-1)?
  
  - **YES**: Perform the following steps *once for each component*:
    
    1. Use the keyboard[2](#footnote-focus-management-2) to **activate the component**, triggering its corresponding page-state transition.
    2. **Observe how focus behaves**. Does browser focus move to an element that preserves the meaning and operability of the page[3](#footnote-focus-management-3)? If not, raise an issue (2.4.3.a).
    3. **Revert the page** to its prior state before testing to the next component.

[\[1\]](#footnote-trigger-focus-management-1): A **page state** is a unique user-interface configuration that corresponds to a specific state of the web application. A new page state occurs when new content is inserted into the page, or existing content is altered in a way that changes the page's functionality and/or meaning.

[\[2\]](#footnote-trigger-focus-management-2): Use *only* the keyboard for this test (do not use a mouse, track pad, or any other pointer device). Common keystrokes you will need to use include: `Tab`, `Shift+Tab`, and arrow keys for **page navigation**; `Enter`, `Space`, and arrow keys for **element interaction**; and `Esc` to **close or dismiss** elements.

[\[3\]](#footnote-trigger-focus-management-3): Keep in mind that focus may not move at all, which is sometimes appropriate.


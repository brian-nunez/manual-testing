### Test #4: Interactive Elements

#### All Interactive Elements

In the next section, you will be asked to systematically move focus from one element to another. As you do so, keep the following questions in mind, and be prepared to raise issues when they become relevant.

- Do user interface components receive focus in an **illogical order**, thereby making it difficult to operate page functionality? If so, raise an issue (2.4.3).
- Are any user interface components[1](#footnote-active-elements-1) **completely skipped** in the natural focus order?
  
  - **YES**: Does the component's underlying function require **mouse input** because it depends on the **path** of the user's movement and not just the endpoints?[2](#footnote-active-elements-2) If not, raise an issue (2.1.1, 2.1.1).
- Does focus become **trapped** within a user interface component?
  
  - **YES**: Can you move focus to, and from, the component using only `Tab`, `Shift + Tab`, unmodified arrow keys, and/or standard exit keys?
    
    - **NO**: Does the page explain how to move focus away from the user interface component?
      
      - **NO**: Raise an issue (2.1.2).

#### Current Interactive Element

Tab through each element on the page. As you focus each **interactive element**, consider the following:

1. Is the element **completely empty**? If so, raise an issue (2.4.3).
2. Is the element **visually hidden** because it is obscured by other content? If so, raise an issue (2.4.11).
3. Do any of the following events occur as a result of **moving focus to the element**? If so, raise an issue.
   
   - A **new window opens** (3.2.1)
   - **Content above your current location changes** in a way that changes the meaning of the page (3.2.1)
   - A **form is submitted** (3.2.1)
   - Focus is **automatically removed** or **redirected** (3.2.1)
4. Does moving focus to the element cause **new content** (such as a tooltip) to appear in the vicinity of the active element?
   
   - Does the content **disappear on its own** shortly after being displayed?
     
     - **YES**: Raise an issue (1.4.13).
     - **NO**: Consider each of the following:
       
       - Can you **actively dismiss** the new content using the **keyboard**? If not, raise an issue (1.4.13).
       - Can you **move the pointer** over the new content without causing the content to disappear as a result? If not, raise an issue (1.4.13).
5. Does the focused element contain any **visible text**?
   
   - **YES**: Compare the visible text to the element's **accessible name**. Does the accessible name contain the same words as the visible text, in the same order, somewhere within it? If not, raise an issue (2.5.3, 2.5.3).
6. Is the focused element a component whose **setting** can be **changed**? In other words, can you change some aspect of the component that will persist once you are no longer interacting with it? Common examples include text fields, checkboxes, radio buttons, select lists, and toggle buttons.
   
   - **YES**: **Change the setting** of the component. Enter text into text fields; toggle checkboxes and radio buttons; navigate through the list of available options in select lists. If a text field is designed to trigger validation when a certain character length is reached, trigger this behavior. Pay attention to any side-effects caused by these interactions. If a **change of context**[3](#footnote-active-elements-3) occurs as a result of changing the setting of the component, and the page **does not warn you** ahead of time, raise an issue (3.2.2, 3.2.2, 3.2.2).
7. Consider the focused element's **mouse** and **keyboard interactions**.
   
   - Does **clicking** the element with the **pointer** produce an action on the **down**[4](#footnote-active-elements-4) event?
     
     - **YES**: Is it **essential**[5](#footnote-active-elements-5) that the function be completed on the down event?
       
       - **NO**: Does the action trigger a **confirmation dialogue**, giving the user the option to abort/undo the action? If not, raise an issue (2.5.2).
   - Are *any* of the following statements true? If so, raise an issue (4.1.2).
     
     - Using the mouse to **click** the element triggers functionality that cannot be triggered using the keyboard.
     - Using the mouse to **hover** over the element triggers functionality that cannot be triggered using the keyboard.
     - Pressing the **`Enter`** , **`Space`** , or **arrow** keys while the element is focused triggers functionality that cannot be triggered using the mouse.
   - Is the element one of the following types of **interactive components** or **widgets**: Accordion, Button, Checkbox, Disclosure, Link, Listbox, Menu, Menu Bar, or Radio Button/Group, Slider, Spinbutton, control within a Toolbar, Tooltip trigger, or Window Splitter?
     
     - **YES**: Are the element's **keyboard interactions** consistent with the [WAI-ARIA Authoring Practices](https://www.w3.org/TR/wai-aria-practices-1.1/) recommendations for that type of component? If not, raise an issue (4.1.2).
8. Perform the following steps:
   
   1. **Move focus** to a different location on the page, making sure that the element being tested no longer has focus.
   2. Using a mouse or pointing device, **hover** the cursor over the element being tested.
   3. Does the text content within the element have a **contrast ratio** of at least 4.5:1 against its background (3:1 for large-scale text)? If not, raise an issue (1.4.3, 1.4.3).

[\[1\]](#footnote-trigger-active-elements-1): A **user interface component** is "a part of the content that is perceived by users as a single control for a distinct function." [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-user-interface-components).

[\[2\]](#footnote-trigger-active-elements-2): "This exception relates to the underlying function, not the input technique. For example, if using handwriting to enter text, the input technique (handwriting) requires path-dependent input but the underlying function (text input) does not." [*WCAG 2.1: Success Criterion 2.1.1 Keyboard*](https://www.w3.org/TR/WCAG21/#keyboard).

[\[3\]](#footnote-trigger-active-elements-3): **Changes of context** are "major changes in the content of the [Web page](https://www.w3.org/TR/WCAG21/#dfn-web-page-s) that, if made without user awareness, can disorient users who are not able to view the entire page simultaneously. Changes in context include changes of: (1) [user agent](https://www.w3.org/TR/WCAG21/#dfn-user-agents), (2) [viewport](https://www.w3.org/TR/WCAG21/#dfn-viewport), (3) focus, and (4) [content](https://www.w3.org/TR/WCAG21/#dfn-content) that changes the meaning of the [Web page](https://www.w3.org/TR/WCAG21/#dfn-web-page-s). **NOTE:** A change of content is not always a change of context. Changes in content, such as an expanding outline, dynamic menu, or a tab control do not necessarily change the context, unless they also change one of the above (e.g., focus)". [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-change-of-context).

[\[4\]](#footnote-trigger-active-elements-4): The "down" event occurs when the mouse button has been pressed down, but has not yet been released.

[\[5\]](#footnote-trigger-active-elements-5): **essential** meaning "if removed, would fundamentally change the information or functionality of the content, and information and functionality cannot be achieved in another way that would conform." [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-essential).

[\[6\]](#footnote-trigger-active-elements-6): **Large-scale text** is text "with at least 18 point \[~24px] or 14 point \[~18.5px] bold or font size that would yield equivalent size for Chinese, Japanese and Korean (CJK) fonts." Note that "\[t]he actual size of the character that a user sees is dependent both on the author-defined size and the user's display or user-agent settings. For many mainstream body text fonts, 14 and 18 point is roughly equivalent to 1.2 and 1.5 em or to 120% or 150% of the default size for body text (assuming that the body font is 100%), but authors would need to check this for the particular fonts in use. When fonts are defined in relative units, the actual point size is calculated by the user agent for display. The point size should be obtained from the user agent, or calculated based on font metrics as the user agent does, when evaluating this success criterion. Users who have low vision would be responsible for choosing appropriate settings." [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-large-scale).

### Test #16: Target Size

#### Target Size

*Reminder*: To perform this test, you must have already completed **axe-core automated tests** and the **Interactive Elements** guided test on the current page state.

1. Open the **axe DevTools extension** and navigate to the saved test for the current page state.
2. Review the issues in the **Overview** tab. Are there any issues whose description reads "Role: The element's role is missing or incorrect"?
   
   - **YES**: For each issue, do either of the following apply to the element?
     
     - The element is a link or control that appears **in a sentence of block of text**.
     - The element is a control where the size of the target is **determined by the user agent and is not modified by the author**. Examples include browser default sized radio buttons, checkboxes, `<select>` elements, date pickers, etc.
       
       - **NO**: Is the size of the element's target[1](#footnote-target-size-1) at least 24 x 24 pixels?
         
         - **NO**: Does the element meet one of the following exception criteria? If not, raise an issue (2.5.8.a).
           
           - **Equivalent**: The element's function can be achieved through a different control on the same page whose target is at least 24 x 24 pixels.
           - **Spacing**: A 24 px diameter circle centered on the target does not touch another target, nor a 24 px diameter circle placed on the center of any other adjacent targets that are also less than 24 by 24 px.

[\[1\]](#footnote-trigger-target-size-1): A **target** is "region of the display that will accept a pointer action, such as the interactive area of a user interface component" [*WCAG 2.2*](https://www.w3.org/TR/WCAG22/#dfn-targets).


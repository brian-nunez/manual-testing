### Test #5: Static Content

1. Does the page contain any **links** that navigate the browser, and that appear in the **context of other static text content** (i.e., not part of an isolated list of navigation links)?
   
   - **YES**: For each link, perform the following steps:
     
     1. Make sure the link is *not* focused.
     2. Determine the color value of the **link text**.
     3. Determine the color value of the **static text** that surrounds the link.
     4. Is the **contrast ratio** between the two values at least **3:1**?
        
        - **NO**: Is the link **visually distinct** from the surrounding text content in a manner **not related to color** (underline, bold, italics, chevron, arrow, outline, etc.). If not, raise an issue (1.4.1).
2. Does the page contain any **informative graphics**? Exclude graphics that are purely decorative and those that have nearby informative text content[1](#footnote-static-content-1) that communicates the same information.
   
   - **YES**: Break the graphic down into the **smallest meaningful pieces**. Each piece is considered a "graphical object".
   - Is the **contrast ratio** of each graphical object against its surrounding background at least 3:1? If not, raise an issue (1.4.11, 1.4.11).
3. Does the page contain any **input fields** with **placeholder text**?
   
   - **YES**: Is the placeholder text **purely decorative**? In other words, if it were completely removed would you still understand the purpose the of the input field?
     
     - **NO**: Is the **contrast ratio** of the placeholder text against its background at least 4.5:1? If not, raise an issue (1.4.3).
4. Does the page contain any **image maps**[4](#footnote-static-content-4)?
   
   - **YES**: For each image map, consider the following:
     
     - Look at the `alt` attribute of each `<area>` tag. Does the same `alt` attribute value appear on multiple `<area>` tags?
       
       - **YES**: Do the `<area>` tags that have the same `alt` value link to the **same destination**?
         
         - **YES**: Is it appropriate for the image map to contain multiple, identical `<area>` tags that link to the same destination? If not, raise an issue (2.4.4).
         - **NO**: Raise an issue (2.4.4).
5. Does the page contain any elements with an **`aria-hidden="true"`** attribute?
   
   - **YES**: Does the element contain any **informative content** that is necessary for understanding the page? If so, raise an issue (1.3.1).
6. Does the page contain any elements with a **`role="presentation"`** attribute?
   
   - Hypothetically, if you simply replaced the element with a basic `<div>` tag, without changing its styling, would any **information** about the **purpose** of the element **be lost**[5](#footnote-static-content-5)? If so, raise an issue (1.3.1).

[\[1\]](#footnote-trigger-static-content-1): **Informative text** must *not* be part of an image and must *not* be contained by an element with an `aria-hidden="true"` attribute.

[\[2\]](#footnote-trigger-static-content-2): The **static text** in question must be stand-alone text content that is not itself part of the background image.

[\[3\]](#footnote-trigger-static-content-3): **Large-scale text** is text "with at least 18 point \[~24px] or 14 point \[~18.5px] bold or font size that would yield equivalent size for Chinese, Japanese and Korean (CJK) fonts." Note that "\[t]he actual size of the character that a user sees is dependent both on the author-defined size and the user's display or user-agent settings. For many mainstream body text fonts, 14 and 18 point is roughly equivalent to 1.2 and 1.5 em or to 120% or 150% of the default size for body text (assuming that the body font is 100%), but authors would need to check this for the particular fonts in use. When fonts are defined in relative units, the actual point size is calculated by the user agent for display. The point size should be obtained from the user agent, or calculated based on font metrics as the user agent does, when evaluating this success criterion. Users who have low vision would be responsible for choosing appropriate settings." [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-large-scale).

[\[4\]](#footnote-trigger-static-content-4): **Image maps** are `<map>` tags that contain multiple `<area>` tags.

[\[5\]](#footnote-trigger-static-content-5): A certain level of accessibility knowledge is required to perform this thought experiment. If you cannot answer this question yourself, ask a more experienced friend or colleague for assistance.


### Test #9: Text Resize, Reflow, and Spacing

Perform the following test procedure **once** to validate text resizing.

1. Set **user agent zoom** to 100%.
2. **Increase user-agent zoom** until all text content **doubles** in size[1](#footnote-reflow-1). If by doing so you cause the page to reach a defined breakpoint and change its layout, that's ok - continue increasing zoom until you reach a breakpoint that allows you to double the size of text content.
3. Is any **content** or **functionality** lost as a result of doubling the size of the text content?
   
   - **YES**: Raise an issue (1.4.4, 1.4.4).

Perform the following test procedure **once** to validate content reflow.

1. Set **user agent zoom** to 100%.
2. Adjust the **viewport width** to 320 pixels.
3. Is **horizontal scrolling** necessary to view content?
   
   - **YES**: Does the content require a **two-dimensional layout** for usage or meaning[2](#footnote-reflow-2)?
     
     - **NO**: Raise an issue (1.4.10).
4. Is any **content** or **functionality** lost as a result of setting the viewport width to 320 pixels?
   
   - **YES**: Raise an issue (1.4.10).

Determine how many **breakpoints** the page contains (breakpoints are viewport-size thresholds at which the layout of the page changes to improve usability on devices with different screen sizes). **Make note** of each breakpoint, and perform the following testing procedure **once for each breakpoint**.

1. Make the viewport width and height as **large as possible** while remaining within the breakpoint you are currently testing. If your page has no breakpoints, or you are testing the largest of its available breakpoints, make the viewport width and height as large as the screen will allow.
2. Set **user agent zoom** to 100%.
3. Run this [text-spacing bookmarklet](https://dylanb.github.io/bookmarklets.html)[3](#footnote-reflow-3) to apply text-spacing changes to the text content.
4. Is any **content** or **functionality** lost as a result of increasing text spacing?
   
   - **YES**: Raise an issue (1.4.12, 1.4.12).
5. If there are **other breakpoints** you still need to test, start again at step #1.

[\[1\]](#footnote-trigger-reflow-1): It may be necessary to increase user-agent zoom beyond 200% in order to cause text content to double in size. Furthermore, not all text may increase in size at the same rate.

[\[2\]](#footnote-trigger-reflow-2): "Examples of content which requires two-dimensional layout are images required for understanding (such as maps and diagrams), video, games, presentations, data tables (not individual cells), and interfaces where it is necessary to keep toolbars in view while manipulating content. It is acceptable to provide two-dimensional scrolling for such parts of the content." [*Success Criterion 1.4.10 Reflow*](https://www.w3.org/TR/WCAG21/#reflow)

[\[3\]](#footnote-trigger-reflow-3): To install the bookmarklet, navigate to the linked page, right-click the link, select "Copy Link Address" and manually create a new browser bookmark, pasting in the contents of the link address as the URL. After doing so, you can activate the bookmark on a page under test to apply the text-spacing changes.


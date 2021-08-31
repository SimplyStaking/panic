import { Component, Host, h } from '@stencil/core';

@Component({
  tag: 'panic-footer',
  styleUrl: 'panic-footer.css'
})
/**
 * Currently panic-footer component is acting as a "page" and being loaded at the URL /daniel.
 * I've added header+content to the rendered JSX/HTML, but what matters here is just the footer.
 */
export class PanicFooter {

  render() {
    return (
      <Host>
        {/* Just ignore this markup */}
        <svc-header headline={"Dummy Page"}></svc-header>
        <svc-content>
          <svc-label>Dummy content...</svc-label>
        </svc-content>
        {/* Just ignore this markup */}

        <svc-footer>
          {/* This is where your code goes... */}
        </svc-footer>
      </Host>
    );
  }

}

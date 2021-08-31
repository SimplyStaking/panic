import { Component, Host, h } from '@stencil/core';

@Component({
  tag: 'panic-header',
  styleUrl: 'panic-header.css',
  shadow: true,
})
export class PanicHeader {

  render() {
    return (
      <Host>
        <slot></slot>
      </Host>
    );
  }

}

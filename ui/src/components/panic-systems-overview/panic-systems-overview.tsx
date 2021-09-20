import { Component, Host, h, Prop } from '@stencil/core';

@Component({
  tag: 'panic-systems-overview'
})
export class PanicSystemsOverview {

  @Prop() chainName: string;

  render() {
    return (
      <Host>
        <panic-header />
        <svc-content-container>
          <h1>Rendering Systems Overview for {this.chainName}</h1>
        </svc-content-container>
      </Host>
    );
  }

}

import { Component, Host, h } from '@stencil/core';
import { createRouter, Route } from 'stencil-router-v2';
const Router = createRouter();

@Component({
  tag: 'panic-root'
})
export class PanicRoot {

  render() {
    return (
      <Host>
        <svc-app>
          <Router.Switch>
            <Route path={"/"}>
              <panic-dashboard-overview />
            </Route>
          </Router.Switch>
        </svc-app>
      </Host>
    );
  }

}

import { Component, Host, h } from '@stencil/core';
import { createRouter, match, Route } from 'stencil-router-v2';
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
            
            <Route path={match('/systems-overview/:chain')} render={(param) => {
              return <panic-systems-overview chainName={param.chain} />
            }}>
            </Route>

          </Router.Switch>
        </svc-app>
      </Host>
    );
  }

}

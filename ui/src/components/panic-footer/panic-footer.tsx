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
  private twitterURL: string = 'https://twitter.com/Simply_VC';
  private githubURL: string = 'https://github.com/SimplyVC';
  private mediumURL: string = 'https://medium.com/simply-vc';
  private telegramURL: string = 'https://t.me/SimplyVC';
  private websiteURL: string = 'https://simply-vc.com.mt';

  render() {
    return (
      <Host>
        {/* Just ignore this markup */}
        <svc-header headline={"Dummy Page"}></svc-header>
        <svc-content>
          <svc-label>Dummy content...</svc-label>
        </svc-content>
        {/* Just ignore this markup */}

        <svc-footer color="primary" headlinePosition="start" headline="Developed by SimplyVC">
          <svc-buttons-container position="end">
            <ion-button target="_blank" href={this.twitterURL}>
              <ion-icon slot="icon-only" name="logo-twitter" href={this.twitterURL}></ion-icon>
            </ion-button>
            <ion-button target="_blank" href={this.githubURL}>
              <ion-icon slot="icon-only" name="logo-github"></ion-icon>
            </ion-button>
            <ion-button target="_blank" href={this.mediumURL}>
              <ion-icon slot="icon-only" name="logo-medium"></ion-icon>
            </ion-button>
            <ion-button target="_blank" href={this.telegramURL}>
              <ion-icon slot="icon-only" src="assets/logos/telegram_logo.svg"></ion-icon>
            </ion-button>
            <ion-button target="_blank" href={this.websiteURL}>
              <ion-icon slot="icon-only" src="assets/logos/simplyvc_logo.svg"></ion-icon>
            </ion-button>
          </svc-buttons-container>
        </svc-footer>
      </Host>
    );
  }

}

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
            <svc-button target="_blank" href={this.twitterURL}>
              <ion-icon name="logo-twitter" class="footer-social"></ion-icon>
            </svc-button>
            <svc-button target="_blank" href={this.githubURL}>
              <ion-icon name="logo-github" class="footer-social"></ion-icon>
            </svc-button>
            <svc-button target="_blank" href={this.mediumURL}>
              <ion-icon name="logo-medium" class="footer-social"></ion-icon>
            </svc-button>
            <svc-button target="_blank" href={this.telegramURL}>
              <ion-icon src="assets/logos/telegram_logo.svg" class="footer-social"></ion-icon>
            </svc-button>
            <svc-button target="_blank" href={this.websiteURL}>
              <ion-icon src="assets/logos/simplyvc_logo.svg" class="footer-social"></ion-icon>
            </svc-button>
          </svc-buttons-container>
        </svc-footer>
      </Host>
    );
  }

}

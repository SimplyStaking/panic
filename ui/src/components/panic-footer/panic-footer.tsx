import { Component, Host, h, getAssetPath } from '@stencil/core';

@Component({
  tag: 'panic-footer',
  styleUrl: 'panic-footer.css',
  assetsDirs: ['assets']
})
export class PanicFooter {
  private twitterURL: string = 'https://twitter.com/Simply_VC';
  private githubURL: string = 'https://github.com/SimplyVC';
  private mediumURL: string = 'https://medium.com/simply-vc';
  private telegramURL: string = 'https://t.me/SimplyVC';
  private websiteURL: string = 'https://simply-vc.com.mt';
  private telegramLogoSVG: string = "telegram_logo.svg"
  private simplyVcLogoSVG: string = "simplyvc_logo.svg"

  render() {
    return (
      <Host>
        <svc-footer color="primary" headline-position="start" headline="Developed by SimplyVC">
          <svc-buttons-container position="end">
            <svc-button icon-name="logo-twitter" href={this.twitterURL} target="_blank"></svc-button>
            <svc-button icon-name="logo-github" href={this.githubURL} target="_blank"></svc-button>
            <svc-button icon-name="logo-medium" href={this.mediumURL} target="_blank"></svc-button>
            <svc-button icon-src={getAssetPath(`./assets/${this.telegramLogoSVG}`)} href={this.telegramURL} target="_blank"></svc-button>
            <svc-button icon-src={getAssetPath(`./assets/${this.simplyVcLogoSVG}`)} href={this.websiteURL} target="_blank"></svc-button>
          </svc-buttons-container>
        </svc-footer>
      </Host>
    );
  }

}

/* eslint-disable react/prefer-stateless-function */
import React, { Component } from 'react';
import Particles from 'react-particles-js';
import Email from 'assets/icons/android-email.png';
import OpsGenie from 'assets/icons/ops-genie-logo.svg';
import PagerDuty from 'assets/icons/pagerduty-logo.png';
import Slack from 'assets/icons/slack-logo.svg';
import Telegram from 'assets/icons/telegram_simple_logo.svg';
import Twilio from 'assets/icons/twilio-logo.svg';

class CustomParticles extends Component {
  render() {
    return (
      <Particles
        frames={30}
        width={window.outerWidth}
        params={{
          particles: {
            collisions: {
              enable: true,
            },
            number: {
              value: 80,
              density: {
                enable: true,
                value_area: 1000,
              },
            },
            opacity: {
              random: {
                enable: true,
                minimumValue: 0.3,
              },
              value: {
                min: 100,
                max: 100,
              },
              animation: {
                count: 0,
                enable: false,
                speed: 0.5,
                sync: false,
                destroy: 'none',
                minimumValue: 0.3,
                startValue: 'random',
              },
            },
            line_linked: {
              blink: false,
              shadow: {
                enable: false,
                color: '#263089',
                blur: 1,
              },
              enable: false,
            },
            move: {
              speed: 0.05,
              out_mode: 'out',
            },
            shape: {
              type: ['image'],
              image: [
                {
                  src: Email,
                  height: 20,
                  width: 20,
                },
                {
                  src: OpsGenie,
                  height: 20,
                  width: 20,
                },
                {
                  src: PagerDuty,
                  height: 20,
                  width: 20,
                },
                {
                  src: Slack,
                  height: 20,
                  width: 20,
                },
                {
                  src: Telegram,
                  height: 20,
                  width: 20,
                },
                {
                  src: Twilio,
                  height: 20,
                  width: 20,
                },
              ],
            },
            color: {
              value: '#263089',
            },
            size: {
              value: 30,
              random: true,
              anim: {
                enable: false,
                speed: 0.1,
                size_min: 5,
                sync: true,
              },
            },
          },
          twinkle: {
            particles: {
              enable: false,
              frequency: 15,
              opacity: 1,
            },
          },
          retina_detect: false,
        }}
      />
    );
  }
}

export default CustomParticles;

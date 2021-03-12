import React from 'react';
// also exported from '@storybook/react' if you can deal with breaking changes in 6.1
import { Story, Meta } from '@storybook/react/types-6-0';
import { baseColors } from '../../theme';

import { DoughnutOverview, DoughnutOverviewProps } from './DoughnutOverview';

export default {
  title: 'DoughnutOverview',
  component: DoughnutOverview,
} as Meta;

const Template: Story<DoughnutOverviewProps> = (args) => <DoughnutOverview {...args} />;

const changePageFunction = () => {
  alert('You are being sent to a page with all the errors!');
}

export const Chainlink = Template.bind({});
Chainlink.args = {
  labelList: ['Critical', 'Info', 'Warning'],
  dataList: [30, 150, 60],
  backgroundColorList: [
    baseColors.critical,
    baseColors.success,
    baseColors.warning,
  ],
  hoverBackgroundColorList: [
    baseColors.critical,
    baseColors.success,
    baseColors.warning,
  ],
  labelPosition: 'right',
  linkTo: changePageFunction
};

export const Cosmos = Template.bind({});
Cosmos.args = {
  labelList: ['Critical', 'Info', 'Warning'],
  dataList: [80, 330, 60],
  backgroundColorList: [
    baseColors.critical,
    baseColors.success,
    baseColors.warning,
  ],
  hoverBackgroundColorList: [
    baseColors.critical,
    baseColors.success,
    baseColors.warning,
  ],
  labelPosition: 'right',
  linkTo: changePageFunction
};

export const Substrate = Template.bind({});
Substrate.args = {
  labelList: ['Critical', 'Info', 'Warning'],
  dataList: [8, 300, 160],
  backgroundColorList: [
    baseColors.critical,
    baseColors.success,
    baseColors.warning,
  ],
  hoverBackgroundColorList: [
    baseColors.critical,
    baseColors.success,
    baseColors.warning,
  ],
  labelPosition: 'right',
  linkTo: changePageFunction
};


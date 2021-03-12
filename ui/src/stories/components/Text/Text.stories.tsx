import React from 'react';
// also exported from '@storybook/react' if you can deal with breaking changes in 6.1
import { Story, Meta } from '@storybook/react/types-6-0';

import { Text, TextProps } from './Text';

export default {
  title: 'Text',
  component: Text,
} as Meta;

const Template: Story<TextProps> = (args) => <Text {...args} />;

export const H1Text = Template.bind({});
H1Text.args = {
  textData: 'H1 Header Text',
  variant: 'h1',
  align: 'left'
}

export const H2Text = Template.bind({});
H2Text.args = {
  textData: 'H2 Header Text',
  variant: 'h2',
  align: 'left'
}

export const H3Text = Template.bind({});
H3Text.args = {
  textData: 'H3 Header Text',
  variant: 'h3',
  align: 'center'
}
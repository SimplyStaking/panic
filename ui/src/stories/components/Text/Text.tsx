import React from 'react';
import { Typography } from '@material-ui/core';

export interface TextProps {

  textData?: string;

  variant?: 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'h5'
  | 'h6'
  | 'subtitle1'
  | 'subtitle2';

  align?: 'inherit'
  | 'left'
  | 'center'
  | 'right'
  | 'justify';
}

export const Text: React.FC<TextProps> = ({
    textData = 'Basic Text',
    variant = "h1",
    align = "center"
  }) => {
  return (
    <Typography
      variant={variant}
      align={align}
    >
      {textData} 
    </Typography>
  );
};

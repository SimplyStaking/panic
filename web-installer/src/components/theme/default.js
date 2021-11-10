import { createTheme } from '@material-ui/core/styles';

// This is used to style tooltips through out all forms.
const defaultTheme = createTheme();
const theme = createTheme({
  overrides: {
    MuiTooltip: {
      tooltip: {
        fontSize: '1em',
        color: 'white',
        backgroundColor: 'black',
      },
    },
  },
});

export { defaultTheme, theme };

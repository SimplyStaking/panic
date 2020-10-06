import { makeStyles, createMuiTheme } from '@material-ui/core/styles';

// This is used to style tooltips through out all forms.
const defaultTheme = createMuiTheme();
const theme = createMuiTheme({
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

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    width: '100%',
  },
}));

export { defaultTheme, theme, useStyles };

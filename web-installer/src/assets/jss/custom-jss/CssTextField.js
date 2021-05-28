import { TextField } from '@material-ui/core';
import { withStyles } from '@material-ui/core/styles';

const CssTextField = withStyles({
  root: {
    '& label.Mui-focused': {
      color: '#000000',
    },
    '& .MuiInput-underline:after': {
      borderBottomColor: '#363946',
    },
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor: '#363946',
      },
      '&:hover fieldset': {
        borderColor: '#363946',
      },
      '&.Mui-focused fieldset': {
        borderColor: '#363946',
      },
    },
  },
})(TextField);

export default CssTextField;

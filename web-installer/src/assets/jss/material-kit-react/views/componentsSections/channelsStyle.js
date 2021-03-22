import { container } from 'assets/jss/material-kit-react.js';
import Background from 'assets/img/backgrounds/background.png';
import { makeStyles } from '@material-ui/core/styles';

const channelStyle = {
  backgroundImage: {
    backgroundImage: `url(${Background})`,
    backgroundRepeat: 'no-repeat',
    backgroundSize: 'cover',
  },
  brand: {
    color: '#FFFFFF',
    textAlign: 'center',
  },
  title: {
    fontSize: '4.2rem',
    fontWeight: '600',
    // display: "inline-block",
    position: 'relative',
    color: '#FFFFFF',
  },
  mainRaised: {
    margin: '-60px 30px 0px',
    borderRadius: '6px',
    boxShadow:
      '0 16px 24px 2px rgba(0, 0, 0, 0.14), 0 6px 30px 5px rgba(0, 0, 0, 0.12), 0 8px 10px -5px rgba(0, 0, 0, 0.2)',
  },
  section: {
    minHeight: '110vh',
    maxHeight: '1600px',
    overflow: 'hidden',
    padding: '70px 0',
    backgroundPosition: 'top center',
    backgroundSize: 'cover',
    margin: '0',
    border: '0',
    display: 'flex',
    alignItems: 'center',
  },
  container,
  form: {
    margin: '0',
  },
  paragraph: {
    textAlign: 'justify',
  },
  cardHeader: {
    background: '#FFFFFF',
    color: '#000000',
    width: 'auto',
    textAlign: 'center',
    marginLeft: '20px',
    marginRight: '20px',
    marginTop: '-40px',
    padding: '20px 0',
    marginBottom: '15px',
  },
  socialIcons: {
    maxWidth: '24px',
    marginTop: '0',
    width: '100%',
    transform: 'none',
    left: '0',
    top: '0',
    height: '100%',
    lineHeight: '41px',
    fontSize: '20px',
  },
  divider: {
    marginTop: '15vh',
    marginBottom: '0px',
    textAlign: 'center',
  },
  cardFooter: {
    paddingTop: '0rem',
    border: '0',
    borderRadius: '6px',
    justifyContent: 'center !important',
  },
  socialLine: {
    marginTop: '1rem',
    textAlign: 'center',
    padding: '0',
  },
  inputIconsColor: {
    color: '#495057',
  },
};

export default makeStyles(channelStyle);

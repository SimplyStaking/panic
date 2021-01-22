import { title } from "assets/jss/material-kit-react.js";
import { makeStyles } from '@material-ui/core/styles';

const productStyle = {
  section: {
    padding: "70px 0",
    textAlign: "center"
  },
  subsection:{
    padding: "45px 0",
    textAlign: "center"
  },
  title: {
    ...title,
    marginBottom: "1rem",
    marginTop: "30px",
    minHeight: "32px",
    textDecoration: "none"
  },
  description: {
    color: "#999"
  },
  root: {
    flexGrow: 1,
  },
  paper: {
    width: '100%',
    textAlign: 'center',
  },
};

export default makeStyles(productStyle);

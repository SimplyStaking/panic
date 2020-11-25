import { container } from "assets/jss/material-kit-react.js";
import Background from "assets/img/backgrounds/5.png"

const componentsStyle = {
  container,
  backgroundImage:{
    backgroundImage: `url(${Background})`,
    backgroundRepeat: 'no-repeat',
    backgroundSize: 'cover',
  },
  brand: {
    color: "#FFFFFF",
    textAlign: "center"
  },
  title: {
    fontSize: "4.2rem",
    fontWeight: "600",
    // display: "inline-block",
    position: "relative",
    color: "#FFFFFF"
  },
  subtitle: {
    fontSize: "1.313rem",
    margin: "10px 0 0"
  },
  mainRaised: {
    margin: "-60px 30px 0px",
    borderRadius: "6px",
    boxShadow:
      "0 16px 24px 2px rgba(0, 0, 0, 0.14), 0 6px 30px 5px rgba(0, 0, 0, 0.12), 0 8px 10px -5px rgba(0, 0, 0, 0.2)"
  },
  link: {
    textDecoration: "none"
  },
  textCenter: {
    textAlign: "center"
  }
};

export default componentsStyle;

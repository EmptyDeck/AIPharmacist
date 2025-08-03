import axios from "axios";
const REACT_APP_SERVER_DOMAIN = process.env.REACT_APP_SERVER_DOMAIN;

export const jsonAxios = axios.create({
  baseURL: process.env.REACT_APP_SERVER_DOMAIN,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
});

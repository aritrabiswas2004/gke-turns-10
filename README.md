# Gemini-powered GKE Cluster Assistant

Using Google's Gemini generative model, this application provides information about a GKE cluster and can also
interact with it all using human-readable commands.

> [!NOTE]
>
> **Licensing Information**
> 
> [microservices-demo](https://github.com/GoogleCloudPlatform/microservices-demo) is an application created by
> the Google Cloud Platform which is under the MIT license. It is included in this repository.
>
> The other portion of this repository is written by the author (me) and is under the Apache v2.0 license

## Deployment

This application is already hosted as a [Streamlit app](https://gke-turns-10.streamlit.app/).

Furthermore, you can see more information on the description website.

## Development Setup

The development setup requires you to have a Gemini API key from Google AI studio, and a (path to a) kubeconfig file (default is in `~/.kube/config`)

You can set the enviroment variables in a `.env` file.

Ensure all dependencies are installed via 

```shell
pip install -r requirements.txt # note: minimum python 3.12 is required.
```

Then run the application by

```shell
streamlit run main.py
```

Alternatively, the [`app/`](./app/) directory is the same as the `main.py` file but uses a more modular structure to make changes in the application easier and more intuitive.

---

_Done as part of the submission for [GKE Turns 10 Hackathon](https://cloud.google.com/blog/topics/training-certifications/join-the-gke-turns-10-hackathon) by Google Cloud._

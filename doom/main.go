/*
 * Copyright 2018 Information Systems Engineering, TU Berlin, Germany
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *                       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * This is being developed for the DITAS Project: https://www.ditas-project.eu/
 */

package main

import (
	"crypto/tls"
	"fmt"
	"io/ioutil"
	"math"
	"strings"
	"sync"

	"encoding/json"
	"flag"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"runtime"
	"time"

	"github.com/sirupsen/logrus"
	"github.com/spf13/pflag"
	"github.com/spf13/viper"
	prefixed "github.com/x-cray/logrus-prefixed-formatter"
	"gopkg.in/yaml.v2"

	"github.com/rakyll/hey/requester"
)

var (
	Build string
)

var logger = logrus.New()
var log *logrus.Entry

func init() {
	if Build == "" {
		Build = "Debug"
	}
	logger.Formatter = new(prefixed.TextFormatter)
	logger.SetLevel(logrus.DebugLevel)
	log = logger.WithFields(logrus.Fields{
		"prefix": "bench",
		"build":  Build,
	})
}

func setup() {
	viper.SetConfigName("bench")
	viper.AddConfigPath(".")

	//setup defaults
	viper.SetDefault("verbose", true)
	viper.SetDefault("workload", "workloads/b0.yml")
	viper.SetDefault("target", "http://localhost:8080")
	viper.SetDefault("data", ".")

	//setup cmd interface
	flag.Bool("verbose", false, "for verbose logging")
	flag.String("workload", "workloads/b0.yml", "the workload descriptor file")
	flag.String("target", "http://localhost:8080", "base url for the benchmark")
	flag.String("data", ".", "base data directory")

	pflag.CommandLine.AddGoFlagSet(flag.CommandLine)
	pflag.Parse()

	err := viper.BindPFlags(pflag.CommandLine)
	if err != nil {
		log.Errorf("error parsing flags %+v", err)
	}

	if viper.GetBool("verbose") {
		logger.SetLevel(logrus.DebugLevel)
	}
}

const user_agent string = "doom/0.0.1"

type DoomWork struct {
	requester.Work
	group *sync.WaitGroup
	name  string
}

type Method struct {
	Name   string
	Path   string
	Method string
}

type Benchmark struct {
	Name     string
	Threads  int
	Requests int
	RPS      float64
	Methods  []Method
}

type Worklaod struct {
	Handler     string
	Duration    int
	BaseURL     string
	KeyCloakURL string
	Username    string
	Password    string
	Benchmarks  []Benchmark
}

func (b *DoomWork) Run() {
	log.Infof("Starting %s", b.name)
	//wrap the original call in a waitGroup
	b.Work.Run()
	log.Infof("%s Done", b.name)
	b.group.Done()
}

func work(num, conc int, RPS float64, url, method, name, token string, group *sync.WaitGroup) *DoomWork {

	log.Debugf("created worker %s with %d %d %f for %s %s", name, num, conc, RPS, method, url)

	// set content-type
	header := make(http.Header)

	header.Set("Content-Type", "text/plain")
	header.Set("Authorization", fmt.Sprintf("Bearer %s", token))
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		log.Fatalf("could not create desired request %s %s: %+v", method, url, err)
	}

	ua := req.UserAgent()
	if ua == "" {
		ua = user_agent
	} else {
		ua += " " + user_agent
	}
	header.Set("User-Agent", ua)
	header.Set("X-DITAS-Benchmark-ID", name)
	req.Header = header

	writer, err := os.OpenFile(fmt.Sprintf("%s.csv", name),
		os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("failed to open results file - %+v", err)
	}

	w := &DoomWork{
		Work: requester.Work{
			Request:            req,
			N:                  num,
			C:                  conc,
			QPS:                RPS,
			Timeout:            30,
			DisableCompression: false,
			DisableKeepAlives:  true,
			DisableRedirects:   false,
			Output:             "csv",
			Writer:             writer,
		},
		group: group,
		name:  name,
	}
	w.Init()

	return w
}

func main() {
	setup()
	http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
	runtime.GOMAXPROCS(8)

	workloadPath := viper.GetString("workload")

	data, err := ioutil.ReadFile(workloadPath)
	if err != nil {
		log.Fatalf("could not read workload@%s - %+v", workloadPath, err)
	}

	var workload Worklaod

	err = yaml.Unmarshal(data, &workload)
	if err != nil {
		log.Fatalf("could not parse workload@%s - %+v", workloadPath, err)
	}

	log.Debugf("using workload:%+v\n", workload)

	if workload.BaseURL == "" {
		workload.BaseURL = viper.GetString("target")
	}

	if workload.Handler == "basic" {
		run(workload)
	} else {
		log.Fatalf("workload is requiring a different handler function %s wich is not yet implemented", workload.Handler)
	}

}

func run(w Worklaod) {
	duration := time.Duration(w.Duration) * time.Minute

	log.Infof("this run is going to take at least %d minutes", duration)

	var waitgroup sync.WaitGroup

	workers := make([]*DoomWork, 0)

	//Cancel Interrupt
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	go func() {
		<-c
		StopAll(workers)
	}()

	for _, bench := range w.Benchmarks {
		requests := bench.Requests
		RPS := bench.RPS
		threads := bench.Threads

		if duration > 0 {
			requests = math.MaxInt32
			if threads <= 0 {
				threads = 1
			}
		} else {
			if requests <= 0 || threads <= 0 {
				requests = 1
				threads = 1
			}
			if requests < threads {
				requests = threads
			}
		}

		token, err := auth(w.KeyCloakURL, w.Username, w.Password)
		if err != nil {
			log.Errorf("Failed to optain authentication token")
		}

		for _, meth := range bench.Methods {
			var url string
			if w.BaseURL == "" {
				url = fmt.Sprintf("%s%s", viper.GetString("target"), meth.Path)
			} else {
				url = fmt.Sprintf("%s%s", w.BaseURL, meth.Path)
			}

			name := fmt.Sprintf("%s/%s-%s-%s", viper.GetString("data"), bench.Name, meth.Name, time.Now().Format(time.RFC3339))
			worker := work(requests, bench.Threads, RPS, url, meth.Method, name,
				token, &waitgroup)
			workers = append(workers, worker)
		}

	}

	if duration > 0 {
		go func() {
			time.Sleep(duration)
			log.Info("reached timeout, terminating workers.")
			StopAll(workers)
		}()
	}

	log.Infof("benchmark ready using %d worker ", len(workers))

	for _, worker := range workers {
		waitgroup.Add(1)
		go worker.Run()
	}

	waitgroup.Wait()

	time.Sleep(100 * time.Millisecond)

	StopAll(workers)
}

type token struct {
	Token     string `json:"access_token"`
	ExpiresIn int    `json:"expires_in"`
}

func auth(path, user, password string) (string, error) {
	//https://<url>:<port>/auth/realms/<blueprint_id>/protocol/openid-connect/token
	data := url.Values{}
	data.Set("username", user)
	data.Set("password", password)
	data.Set("grant_type", "password")
	data.Set("client_id", "vdc_client")

	req, err := http.Post(path, "application/x-www-form-urlencoded", strings.NewReader(data.Encode()))
	if err != nil {
		log.Debugf("auth request failed with %+v", err)
		return "", err
	}

	if req.StatusCode > 200 {
		log.Debugf("auth request failed with status %d", req.StatusCode)
		return "", fmt.Errorf("Unauthrozied request %d", req.StatusCode)
	}

	tokenData, err := ioutil.ReadAll(req.Body)

	if err != nil {
		log.Debugf("failed to parse %+v", err)
		return "", err
	}
	token := token{}
	err = json.Unmarshal(tokenData, &token)
	if err != nil {
		log.Debugf("failed to parse %+v", err)
		return "", err
	}
	log.Infof("got token successfully %d %s", token.ExpiresIn, token.Token)
	return token.Token, nil
}

func StopAll(workers []*DoomWork) {
	log.Infof("closing all workers")

	for _, worker := range workers {
		worker.Stop()
	}
}
